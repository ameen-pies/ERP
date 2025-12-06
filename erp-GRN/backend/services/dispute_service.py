from datetime import datetime

from backend.utils.database import get_db
from backend.utils.po_adapter import internal_po_to_bons_commande
from backend.utils.serializers import serialize_doc


async def create_dispute(
    po_id: str,
    grn_reference: str,
    line_id: str,
    issue_type: str,
    message: str,
    excess_qty: int = 0,
) -> dict:
    """Store disputes derived from GRN anomalies."""
    db = get_db()
    doc = {
        "po_id": po_id,
        "grn_reference": grn_reference,  # Use reference instead of ID
        "line_id": line_id,
        "issue_type": issue_type,
        "message": message,  # Detailed message explaining the problem
        "excess_qty": excess_qty,  # Quantity to return for over-delivery
        "status": "open",
        "created_at": datetime.utcnow(),
    }
    result = await db["disputes"].insert_one(doc)
    dispute = await db["disputes"].find_one({"_id": result.inserted_id})
    return serialize_doc(dispute)


async def resolve_dispute(dispute_id: str) -> dict:
    """Mark a dispute as resolved, add accepted quantity to stock ledger, and send validation emails."""
    from bson import ObjectId
    from backend.utils.email_service import (
        send_grn_validation_to_buyer,
        send_grn_validation_to_supplier,
    )
    from backend.services.stock_service import record_stock_movement
    
    db = get_db()
    updated = await db["disputes"].find_one_and_update(
        {"_id": ObjectId(dispute_id)},
        {"$set": {"status": "resolved", "resolved_at": datetime.utcnow()}},
        return_document=True,
    )
    if not updated:
        raise ValueError("Dispute not found.")
    
    # Get GRN and PO details for email
    grn_reference = updated.get("grn_reference", "Unknown")
    po_id = updated.get("po_id")
    issue_type = updated.get("issue_type")
    
    # For over-delivery disputes with good quality, add accepted quantity to stock ledger
    if issue_type == "Over-delivery" and po_id:
        try:
            # Find the GRN to get the accepted quantity
            grn_doc = await db["grns"].find_one({"reference": grn_reference})
            if grn_doc:
                line_id = updated.get("line_id")
                # Find the line in GRN that matches this dispute
                for grn_line in grn_doc.get("lines", []):
                    if grn_line.get("po_line_id") == line_id:
                        # Check if stock was already recorded (should be recorded during GRN creation)
                        # But if not, record it now
                        item_name = grn_line.get("item_name", "Unknown")
                        accepted_qty = grn_line.get("accepted_qty", 0)
                        
                        # Check if stock entry already exists for this GRN and item
                        existing_stock = await db["stock_ledger"].find_one({
                            "reference": grn_reference,
                            "item_name": item_name
                        })
                        
                        # Only add to stock if not already recorded (shouldn't happen, but safety check)
                        if not existing_stock and accepted_qty > 0:
                            await record_stock_movement(
                                item_name, accepted_qty, grn_reference
                            )
                        break
        except Exception as e:
            import logging
            logging.error(f"Error adding stock for resolved dispute: {e}")
            pass  # Don't fail dispute resolution if stock recording fails
    
    # Get PO details
    if po_id:
        try:
            from backend.services.po_service import get_purchase_order
            po = await get_purchase_order(po_id)
            po_number = po.get("po_number", "Unknown")
            supplier_name = po.get("supplier", "Supplier")
            
            # Get supplier email from PO
            from backend.utils.database import get_db as get_db_func
            db_po = get_db_func()
            bons_doc = await db_po["bons_commande"].find_one({"_id": ObjectId(po_id)})
            supplier_email = None
            if bons_doc:
                supplier_name = bons_doc.get("fournisseur", {}).get("nom", supplier_name)
                supplier_email = bons_doc.get("fournisseur", {}).get("email")
            
            # Send validation emails in background (non-blocking)
            import threading
            def send_validation_emails():
                try:
                    send_grn_validation_to_buyer(
                        grn_reference=grn_reference,
                        po_number=po_number,
                        supplier_name=supplier_name,
                    )
                    send_grn_validation_to_supplier(
                        grn_reference=grn_reference,
                        po_number=po_number,
                        supplier_name=supplier_name,
                        supplier_email=supplier_email,
                    )
                except Exception:
                    pass  # Don't fail dispute resolution if email fails
            
            email_thread = threading.Thread(target=send_validation_emails, daemon=True)
            email_thread.start()
            
            # Check if PO should be closed after dispute resolution
            await check_and_close_po_if_complete(po_id)
        except Exception:
            pass  # Don't fail dispute resolution if email fails
    
    return serialize_doc(updated)


async def verify_receipt(dispute_id: str) -> dict:
    """
    Verify receipt of returned items for over-delivery or quality failure disputes.
    This automatically resolves the dispute when supplier confirms receipt.
    """
    from bson import ObjectId
    
    db = get_db()
    dispute = await db["disputes"].find_one({"_id": ObjectId(dispute_id)})
    if not dispute:
        raise ValueError("Dispute not found.")
    
    # Check if dispute is already resolved
    if dispute.get("status") == "resolved":
        raise ValueError("This dispute has already been resolved.")
    
    # Check if it's an over-delivery or quality failure dispute
    issue_type = dispute.get("issue_type")
    if issue_type not in ["Over-delivery", "Quality failure"]:
        raise ValueError("This verification is only for over-delivery or quality failure disputes.")
    
    # Resolve the dispute (this will also send validation emails and check PO status)
    return await resolve_dispute(dispute_id)


async def check_and_close_po_if_complete(po_id: str) -> None:
    """Check if all disputes are resolved and all PO lines are fully received, then close the PO."""
    from bson import ObjectId
    from backend.services.po_service import evaluate_po_status, get_purchase_order
    from backend.utils.po_adapter import internal_po_to_bons_commande, bons_commande_to_internal_po
    
    try:
        db = get_db()
        
        # Get PO from database directly to ensure we have latest data
        bons_doc = await db["bons_commande"].find_one({"_id": ObjectId(po_id)})
        if not bons_doc:
            return
        
        # Convert to internal format
        po = bons_commande_to_internal_po(bons_doc)
        
        # Check if all lines are fully received (qty_received >= qty_ordered)
        all_lines_closed = all(
            line.get("qty_received", 0) >= line.get("qty_ordered", 0)
            for line in po.get("lines", [])
        )
        
        # Check if all disputes for this PO are resolved
        open_disputes = await db["disputes"].count_documents(
            {"po_id": po_id, "status": "open"}
        )
        
        # Close PO if all lines are received and no open disputes
        if all_lines_closed and open_disputes == 0:
            # Update PO status in database
            await db["bons_commande"].update_one(
                {"_id": ObjectId(po_id)},
                {"$set": {"status": "closed"}},
            )
    except Exception as e:
        # Log error but don't break dispute resolution
        import logging
        logging.error(f"Error checking PO status: {e}")
        pass


async def delete_dispute(dispute_id: str) -> dict:
    """Delete a dispute."""
    from bson import ObjectId
    db = get_db()
    result = await db["disputes"].delete_one({"_id": ObjectId(dispute_id)})
    if result.deleted_count == 0:
        raise ValueError("Dispute not found.")
    return {"deleted": True, "dispute_id": dispute_id}


async def list_disputes() -> list[dict]:
    """Return all recorded disputes sorted newest first."""
    db = get_db()
    cursor = db["disputes"].find().sort("created_at", -1)
    disputes = []
    async for doc in cursor:
        disputes.append(serialize_doc(doc))
    return disputes

