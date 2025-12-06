import threading
from datetime import datetime
from typing import Optional

from bson import ObjectId

from backend.models.grn_models import CreateGRNRequest, UpdateGRNRequest
from backend.services.dispute_service import create_dispute
from backend.services.po_service import evaluate_po_status
from backend.services.stock_service import record_stock_movement
from backend.utils.database import get_db
from backend.utils.email_service import (
    send_grn_error_to_buyer,
    send_grn_error_to_supplier,
    send_grn_validation_to_buyer,
    send_grn_validation_to_supplier,
    send_under_delivery_notification_to_buyer,
    send_under_delivery_notification_to_supplier,
    send_over_delivery_notification_to_supplier,
    send_grn_notification_to_buyer,
    send_grn_issues_notification_to_supplier,
)
from backend.utils.po_adapter import bons_commande_to_internal_po, internal_po_to_bons_commande
from backend.utils.serializers import serialize_doc


def _normalize_quality_status(value: str) -> str:
    return value.strip().lower() if isinstance(value, str) else "pass"


async def create_grn(payload: CreateGRNRequest) -> dict:
    """Save a GRN, update PO progress, track stock, and flag anomalies."""
    db = get_db()
    po_collection = db["bons_commande"]

    bons_doc = await po_collection.find_one({"_id": ObjectId(payload.po_id)})
    if not bons_doc:
        raise ValueError("Purchase Order not found.")

    # Convert to internal format for processing
    po_doc = bons_commande_to_internal_po(bons_doc)
    po_reference = po_doc.get("po_number", "N/A")  # Get PO reference for faster lookup
    line_lookup = {line["line_id"]: line for line in po_doc.get("lines", [])}
    grn_lines = []
    anomalies = []

    grn_reference = f"GRN-{int(datetime.utcnow().timestamp())}"
    has_disputes = False  # Track if disputes need to be created
    under_deliveries = []  # Track under-delivery cases for notifications

    for line in payload.lines:
        po_line = line_lookup.get(line.po_line_id)
        if not po_line:
            raise ValueError(f"PO line {line.po_line_id} could not be matched.")

        qty_ordered = po_line["qty_ordered"]
        qty_received = line.received_qty
        current_received = po_line.get("qty_received", 0)
        total_received_after_grn = current_received + qty_received
        remaining_qty = max(qty_ordered - current_received, 0)
        quality_status = _normalize_quality_status(line.quality_status)
        accepted_qty = 0  # Will be set only for normal deliveries

        # UPDATED LOGIC:
        # 1. If quality is BAD -> Reject immediately, return ALL received items, create dispute, notify both parties
        # 2. If quality is GOOD:
        #    - Calculate total received (current_received + qty_received)
        #    - If total_received > qty_ordered: Over-delivery - return excess, create dispute, notify both parties
        #    - If total_received <= qty_ordered: Accept quantity, update PO

        if quality_status != "pass":
            # Quality failed - reject immediately, return ALL received items, create dispute
            has_disputes = True
            # Return ALL qty_received in this GRN (not accepted into stock)
            anomalies.append(
                {
                    "line_id": line.po_line_id,
                    "issue_type": "Quality failure",
                    "item_name": po_line.get("item_name", "Unknown"),
                    "message": f"Quality inspection failed for item '{po_line.get('item_name', 'Unknown')}'. All {qty_received} unit(s) rejected and returned.",
                    "details": f"Item: {po_line.get('item_name', 'Unknown')}, Ordered: {qty_ordered}, Previously Received: {current_received}, Received in this GRN: {qty_received}, Quality Status: FAIL. All {qty_received} unit(s) from this delivery have been rejected and returned to supplier.",
                    "qty_to_return": qty_received,  # Return all received items
                    "current_received": current_received,
                    "qty_received": qty_received,
                    "qty_ordered": qty_ordered,
                }
            )
        elif total_received_after_grn > qty_ordered:
            # Over-delivery with good quality - accept up to ordered quantity, close PO line, create dispute
            has_disputes = True
            excess = total_received_after_grn - qty_ordered
            # Accept only the ordered quantity (quality is good)
            accepted_qty = qty_ordered - current_received  # Accept only what's needed
            po_line["qty_received"] = qty_ordered  # Set to ordered quantity (fully received)
            po_line["status"] = "closed"  # Close the line since we received the full ordered quantity
            
            # Record stock movement for accepted quantity (only the ordered amount)
            if accepted_qty > 0:
                await record_stock_movement(
                    po_line["item_name"], accepted_qty, grn_reference
                )
            
            # The excess is what needs to be returned
            anomalies.append(
                {
                    "line_id": line.po_line_id,
                    "issue_type": "Over-delivery",
                    "item_name": po_line.get("item_name", "Unknown"),
                    "message": f"Total received ({total_received_after_grn} units) exceeds ordered quantity ({qty_ordered} units). Excess: {excess} units.",
                    "details": f"Item: {po_line.get('item_name', 'Unknown')}, Ordered: {qty_ordered}, Previously Received: {current_received}, Received in this GRN: {qty_received}, Total Received: {total_received_after_grn}, Excess: {excess} units. {excess} unit(s) have been returned to supplier.",
                    "qty_to_return": excess,  # Return only the excess
                    "current_received": current_received,
                    "qty_received": qty_received,
                    "total_received": total_received_after_grn,
                    "qty_ordered": qty_ordered,
                    "accepted_qty": accepted_qty,  # Store accepted quantity for dispute resolution
                }
            )
        elif qty_received > remaining_qty:
            # This GRN delivery exceeds remaining quantity (shouldn't happen if logic is correct, but keep as safety check)
            has_disputes = True
            excess = qty_received - remaining_qty
            # Accept only the remaining quantity (quality is good)
            accepted_qty = remaining_qty
            po_line["qty_received"] = qty_ordered  # Set to ordered quantity (fully received)
            po_line["status"] = "closed"  # Close the line since we received the full ordered quantity
            
            # Record stock movement for accepted quantity
            if accepted_qty > 0:
                await record_stock_movement(
                    po_line["item_name"], accepted_qty, grn_reference
                )
            
            anomalies.append(
                {
                    "line_id": line.po_line_id,
                    "issue_type": "Over-delivery",
                    "item_name": po_line.get("item_name", "Unknown"),
                    "message": f"Delivered quantity ({qty_received}) exceeds remaining open quantity ({remaining_qty}).",
                    "details": f"Item: {po_line.get('item_name', 'Unknown')}, Ordered: {qty_ordered}, Previously Received: {current_received}, Remaining: {remaining_qty}, Received in this GRN: {qty_received}, Excess: {excess} units. {excess} unit(s) have been returned to supplier.",
                    "qty_to_return": excess,
                    "current_received": current_received,
                    "qty_received": qty_received,
                    "total_received": current_received + qty_received,
                    "qty_ordered": qty_ordered,
                    "accepted_qty": accepted_qty,  # Store accepted quantity for dispute resolution
                }
            )
        else:
            # Quality passed AND (qty_received <= qty_ordered) - Update quantities
            # This includes under-delivery (qty_received < qty_ordered) - update and keep PO pending
            accepted_qty = min(qty_received, remaining_qty)
            po_line["qty_received"] = current_received + accepted_qty
            po_line["status"] = (
                "closed"
                if po_line["qty_received"] >= po_line["qty_ordered"]
                else "open"
            )
            
            # Track under-delivery for notification (no dispute)
            # Only flag as under-delivery if there's still remaining quantity AFTER this GRN
            # This prevents false positives when a partial delivery completes the order
            final_remaining_after_grn = max(qty_ordered - (current_received + accepted_qty), 0)
            if final_remaining_after_grn > 0:
                # There's still remaining quantity, so this was an under-delivery
                shortfall = final_remaining_after_grn
                under_deliveries.append({
                    "line_id": line.po_line_id,
                    "item_name": po_line.get("item_name", "Unknown"),
                    "qty_ordered": qty_ordered,
                    "qty_received": qty_received,
                    "current_received": current_received,
                    "total_received_after_grn": current_received + accepted_qty,
                    "remaining_after_grn": final_remaining_after_grn,
                    "shortfall": shortfall,
                })
            
            # Record stock movement for accepted quantity
            if accepted_qty > 0:
                await record_stock_movement(
                    po_line["item_name"], accepted_qty, grn_reference
                )

        # Calculate remaining quantity after this GRN
        # For quality failures and over-deliveries, we don't accept the quantity
        # So total_received stays at current_received (not updated)
        # For normal deliveries, total_received = current_received + accepted_qty
        if quality_status != "pass" or total_received_after_grn > qty_ordered or qty_received > remaining_qty:
            # Quality failed or over-delivery - don't update total_received
            final_received = current_received
        else:
            # Normal delivery - update total_received
            final_received = current_received + accepted_qty
        
        final_remaining = max(qty_ordered - final_received, 0)
        
        grn_lines.append(
            {
                "po_line_id": line.po_line_id,
                "item_name": po_line.get("item_name", "Unknown"),
                "delivery_expected_qty": remaining_qty,  # What was expected/remaining before this GRN
                "received_qty": qty_received,  # What was actually received in this GRN
                "accepted_qty": accepted_qty,  # What was accepted into stock
                "qty_ordered": qty_ordered,  # Total ordered on PO
                "current_received": current_received,  # Previously received before this GRN
                "total_received": final_received,  # Total after this GRN (correctly calculated)
                "quality_status": quality_status,
                "comments": line.comments,
                "remaining_qty": final_remaining,  # Remaining after this GRN (based on total_received)
            }
        )

    # Update PO status and quantities (always update, even if under-delivered)
    po_doc["status"] = evaluate_po_status(po_doc["lines"])
    
    # Convert back to bons_commande format for update
    bons_commande_update = internal_po_to_bons_commande(po_doc)
    await po_collection.update_one(
        {"_id": ObjectId(payload.po_id)},
        {"$set": {"lignes": bons_commande_update["lignes"], "status": bons_commande_update["status"]}},
    )

    # Determine GRN status: "pending" if there are disputes (over-delivery or quality issues), otherwise "registered"
    # Note: Under-delivery does NOT create disputes, so GRN can be "registered" even if quantities don't match
    grn_status = "pending" if has_disputes else "registered"
    
    grn_doc = {
        "po_id": payload.po_id,
        "po_reference": po_reference,  # Store PO reference for faster lookup
        "reference": grn_reference,
        "lines": grn_lines,
        "status": grn_status,
        "created_at": datetime.utcnow(),
    }

    result = await db["grns"].insert_one(grn_doc)
    grn_saved = await db["grns"].find_one({"_id": result.inserted_id})

    # Create disputes for anomalies (over-delivery and quality issues, NOT under-delivery)
    dispute_ids = {}  # Store dispute IDs for verification emails (both over-delivery and quality failures)
    dispute_details = {}  # Store dispute details for email notifications
    if anomalies:
        for anomaly in anomalies:
            # Find the corresponding GRN line to get quantity details
            grn_line = next(
                (line for line in grn_lines if line["po_line_id"] == anomaly["line_id"]),
                None
            )
            
            # Get quantity to return from anomaly (already calculated correctly)
            excess_qty = anomaly.get("qty_to_return", 0)
            
            # Use detailed message if available
            dispute_message = anomaly.get("details", anomaly["message"])
            
            dispute = await create_dispute(
                po_id=payload.po_id,
                grn_reference=grn_reference,  # Use reference instead of ID
                line_id=anomaly["line_id"],
                issue_type=anomaly["issue_type"],
                message=dispute_message,  # Use detailed message
                excess_qty=excess_qty,  # Add excess quantity for over-delivery
            )
            
            # Store dispute ID for verification emails (both over-delivery and quality failures)
            dispute_id = dispute.get("_id")
            if dispute_id:
                dispute_ids[anomaly["line_id"]] = str(dispute_id)
                # Get details from anomaly (most accurate) or fallback to grn_line
                dispute_details[anomaly["line_id"]] = {
                    "dispute_id": str(dispute_id),
                    "issue_type": anomaly["issue_type"],
                    "item_name": anomaly.get("item_name") or (grn_line.get("item_name", "Unknown") if grn_line else "Unknown"),
                    "qty_received": anomaly.get("qty_received", grn_line.get("received_qty", 0) if grn_line else 0),
                    "qty_ordered": anomaly.get("qty_ordered", grn_line.get("qty_ordered", 0) if grn_line else 0),
                    "current_received": anomaly.get("current_received", 0),
                    "total_received": anomaly.get("total_received", anomaly.get("current_received", 0) + anomaly.get("qty_received", 0)),
                    "excess_qty": excess_qty,
                    "qty_to_return": excess_qty,
                    "accepted_qty": anomaly.get("accepted_qty", 0),  # Store accepted quantity for dispute resolution
                    "quality_status": grn_line.get("quality_status", "fail" if anomaly["issue_type"] == "Quality failure" else "pass") if grn_line else ("fail" if anomaly["issue_type"] == "Quality failure" else "pass"),
                }
    
    # Send email notifications in background (non-blocking)
    # ALWAYS send emails for every GRN - both to buyer and supplier
    po_number = bons_doc.get("purchase_order_id", "Unknown")
    supplier_name = bons_doc.get("fournisseur", {}).get("nom", "Supplier")
    # Get supplier email, default to None if not provided (email functions will use RESPONSIBLE_EMAIL)
    supplier_email = bons_doc.get("fournisseur", {}).get("email") or None
    
    def send_emails_background():
        try:
            # Always send comprehensive GRN notification to buyer with all details
            # Include anomalies if there are any
            send_grn_notification_to_buyer(
                grn_reference=grn_reference,
                po_number=po_number,
                supplier_name=supplier_name,
                grn_lines=grn_lines,
                grn_status=grn_status,
                anomalies=anomalies if has_disputes else [],
            )
            
            # Handle under-delivery notifications (no disputes)
            for under_delivery in under_deliveries:
                send_under_delivery_notification_to_buyer(
                    grn_reference=grn_reference,
                    po_number=po_number,
                    supplier_name=supplier_name,
                    item_name=under_delivery["item_name"],
                    qty_ordered=under_delivery["qty_ordered"],
                    qty_received=under_delivery["qty_received"],
                    current_received=under_delivery.get("current_received", 0),
                    total_received=under_delivery.get("total_received_after_grn", 0),
                    remaining_qty=under_delivery.get("remaining_after_grn", 0),
                    shortfall=under_delivery["shortfall"],
                )
                send_under_delivery_notification_to_supplier(
                    grn_reference=grn_reference,
                    po_number=po_number,
                    supplier_name=supplier_name,
                    item_name=under_delivery["item_name"],
                    qty_ordered=under_delivery["qty_ordered"],
                    qty_received=under_delivery["qty_received"],
                    current_received=under_delivery.get("current_received", 0),
                    total_received=under_delivery.get("total_received_after_grn", 0),
                    remaining_qty=under_delivery.get("remaining_after_grn", 0),
                    shortfall=under_delivery["shortfall"],
                    supplier_email=supplier_email,
                )
            
            # Handle disputes (over-delivery and quality issues)
            if has_disputes:
                # Send comprehensive issues notification to supplier with all errors and verification buttons
                if dispute_details:
                    send_grn_issues_notification_to_supplier(
                        grn_reference=grn_reference,
                        po_number=po_number,
                        supplier_name=supplier_name,
                        dispute_details=list(dispute_details.values()),
                        supplier_email=supplier_email,
                    )
                
                # Still send error emails to buyer for all issues
                for anomaly in anomalies:
                    error_type = anomaly["issue_type"]
                    send_grn_error_to_buyer(
                        grn_reference=grn_reference,
                        po_number=po_number,
                        supplier_name=supplier_name,
                        error_type=error_type,
                        error_details=anomaly.get("details", anomaly["message"]),
                    )
            elif not under_deliveries:
                # Send validation emails only if no disputes and no under-deliveries
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
        except Exception as e:
            import traceback
            print(f"ERROR: Failed to send emails in background thread:")
            print(f"Error: {str(e)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            # Don't fail GRN creation if email fails
    
    # Start email in background thread
    email_thread = threading.Thread(target=send_emails_background, daemon=True)
    email_thread.start()

    return {
        "grn": serialize_doc(grn_saved),
        "po": serialize_doc(po_doc),
        "anomalies": anomalies,
    }


def _build_search_query(search: Optional[str], fields: list[str]) -> dict | None:
    """Helper to search GRN fields with a regex when a value is provided."""
    if not search:
        return None
    regex = {"$regex": search, "$options": "i"}
    return {"$or": [{field: regex} for field in fields]}


async def list_grns(search: Optional[str] = None) -> list[dict]:
    """Return all GRNs for dashboard opinions (filtered if required)."""
    db = get_db()
    fields = ["reference", "status", "po_id", "lines.item_name", "lines.line_id"]
    query = _build_search_query(search, fields) or {}
    cursor = db["grns"].find(query).sort("created_at", -1)
    records = []
    async for doc in cursor:
        records.append(serialize_doc(doc))
    return records


async def update_grn(grn_id: str, payload: UpdateGRNRequest) -> dict:
    """Allow minor updates to GRN metadata such as status/comments."""
    db = get_db()
    grn_doc = await db["grns"].find_one({"_id": ObjectId(grn_id)})
    if not grn_doc:
        raise ValueError("GRN not found.")

    updates: dict = {}
    if payload.status:
        updates["status"] = payload.status

    if payload.lines:
        for line in grn_doc["lines"]:
            changes = next(
                (entry for entry in payload.lines if entry.po_line_id == line["po_line_id"]),
                None,
            )
            if changes:
                if changes.quality_status:
                    line["quality_status"] = changes.quality_status
                if changes.comments is not None:
                    line["comments"] = changes.comments
        updates["lines"] = grn_doc["lines"]

    if not updates:
        return serialize_doc(grn_doc)

    await db["grns"].update_one({"_id": ObjectId(grn_id)}, {"$set": updates})
    updated = await db["grns"].find_one({"_id": ObjectId(grn_id)})
    return serialize_doc(updated)


async def delete_grn(grn_id: str) -> dict:
    """Delete a GRN while rolling back stock and PO receipts."""
    db = get_db()
    grn_doc = await db["grns"].find_one({"_id": ObjectId(grn_id)})
    if not grn_doc:
        raise ValueError("GRN not found.")

    bons_doc = await db["bons_commande"].find_one(
        {"_id": ObjectId(grn_doc["po_id"])}
    )
    if bons_doc:
        # Convert to internal format
        po_doc = bons_commande_to_internal_po(bons_doc)
        for line in grn_doc["lines"]:
            for po_line in po_doc["lines"]:
                if po_line["line_id"] == line["po_line_id"]:
                    po_line["qty_received"] = max(
                        po_line["qty_received"] - line["accepted_qty"], 0
                    )
                    po_line["status"] = (
                        "closed"
                        if po_line["qty_received"] >= po_line["qty_ordered"]
                        else "open"
                    )
        po_doc["status"] = evaluate_po_status(po_doc["lines"])
        # Convert back to bons_commande format
        bons_commande_update = internal_po_to_bons_commande(po_doc)
        await db["bons_commande"].update_one(
            {"_id": ObjectId(po_doc["_id"])},
            {"$set": {"lignes": bons_commande_update["lignes"], "status": bons_commande_update["status"]}},
        )

    await db["stock_ledger"].delete_many({"reference": grn_doc["reference"]})
    await db["disputes"].delete_many({"grn_id": grn_id})
    await db["grns"].delete_one({"_id": ObjectId(grn_id)})
    return {"deleted": True}

