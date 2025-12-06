from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from bson import ObjectId
from pymongo import ReturnDocument

from backend.models.po_models import (
    AddPOLineRequest,
    CreatePORequest,
    POLineUpdate,
    UpdatePORequest,
)
from backend.utils.database import get_db
from backend.utils.po_adapter import (
    bons_commande_to_internal_po,
    internal_po_to_bons_commande,
)
from backend.utils.serializers import serialize_doc


def evaluate_po_status(lines: list[dict]) -> str:
    """Determine PO status based on the per-line progress.
    Returns 'closed' if all lines are fully received, otherwise 'pending'.
    """
    if not lines:
        return "pending"
    if all(line.get("qty_received", 0) >= line.get("qty_ordered", 0) for line in lines):
        return "closed"
    return "pending"


def _build_po_line(payload_line: AddPOLineRequest | dict) -> dict:
    """Normalize a line payload into the stored format."""

    def _value(field: str, default):
        if isinstance(payload_line, dict):
            return payload_line.get(field, default)
        return getattr(payload_line, field, default)

    return {
        "line_id": str(uuid4()),
        "item_name": _value("item_name", "Unknown Item"),
        "qty_ordered": _value("qty_ordered", 1),
        "unit_price": _value("unit_price", 0.0),
        "qty_received": 0,
        "status": "open",
    }


async def create_purchase_order(payload: CreatePORequest) -> dict:
    """Persist a new PO with its lines."""
    if not payload.lines:
        raise ValueError("At least one PO line is required.")

    db = get_db()
    await db["suppliers"].update_one(
        {"name": payload.supplier},
        {
            "$set": {
                "name": payload.supplier,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )
    
    # Build internal format lines
    lines = [_build_po_line(line) for line in payload.lines]
    
    # Convert to bons_commande format
    lignes = []
    for idx, line in enumerate(lines):
        lignes.append({
            "description": line["item_name"],
            "quantite": line["qty_ordered"],
            "prix_unitaire": line["unit_price"],
            "montant_ligne": line["qty_ordered"] * line["unit_price"],
            "unite": "unité",
            "numero_ligne": idx + 1,
            "reference_catalogue": "",
            "specifications_techniques": None,
            "qty_received": 0,
            "status": "open",
        })
    
    po_doc = {
        "purchase_order_id": f"BC-{int(datetime.utcnow().timestamp())}",
        "fournisseur": {
            "nom": payload.supplier,
            "email": None,
            "telephone": None,
        },
        "status": evaluate_po_status(lines),
        "lignes": lignes,
        "date_creation": datetime.utcnow().isoformat(),
        "linked_pr_id": "",
        "details_demande": "",
        "justification": "",
        "type_achat": "Produit",
        "devise": "TND",
        "montant_total_ht": sum(l["montant_ligne"] for l in lignes),
        "montant_tva": 0,
        "montant_total_ttc": sum(l["montant_ligne"] for l in lignes),
    }

    result = await db["bons_commande"].insert_one(po_doc)
    inserted = await db["bons_commande"].find_one({"_id": result.inserted_id})
    
    # Return in internal format
    internal_po = bons_commande_to_internal_po(inserted)
    return serialize_doc(internal_po)


async def add_line_to_po(po_id: str, payload: AddPOLineRequest) -> dict:
    """Append a new line to an existing PO."""
    db = get_db()
    po_collection = db["bons_commande"]
    # Get existing PO and convert to internal format
    bons_doc = await po_collection.find_one({"_id": ObjectId(po_id)})
    if not bons_doc:
        raise ValueError("PO not found.")
    
    internal_po = bons_commande_to_internal_po(bons_doc)
    new_line = _build_po_line(payload)
    internal_po["lines"].append(new_line)
    
    # Convert new line to bons_commande format
    new_ligne = {
        "description": new_line["item_name"],
        "quantite": new_line["qty_ordered"],
        "prix_unitaire": new_line["unit_price"],
        "montant_ligne": new_line["qty_ordered"] * new_line["unit_price"],
        "unite": "unité",
        "numero_ligne": len(internal_po["lines"]),
        "reference_catalogue": "",
        "specifications_techniques": None,
        "qty_received": 0,
        "status": "open",
    }
    
    # Update in bons_commande format
    status = evaluate_po_status(internal_po["lines"])
    updated = await po_collection.find_one_and_update(
        {"_id": ObjectId(po_id)},
        {
            "$push": {"lignes": new_ligne},
            "$set": {"status": status}
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise ValueError("PO not found.")
    
    # Return in internal format
    internal_po = bons_commande_to_internal_po(updated)
    return serialize_doc(internal_po)


def _build_search_query(search: Optional[str], fields: list[str]) -> dict | None:
    """Create a regex query over the provided fields when search is present."""
    if not search:
        return None
    regex = {"$regex": search, "$options": "i"}
    return {"$or": [{field: regex} for field in fields]}


async def list_purchase_orders(
    search: Optional[str] = None, 
    status_filter: Optional[str] = None,
    has_remaining: Optional[bool] = None
) -> list[dict]:
    """Return all POs sorted by creation (with optional filtering).
    
    Args:
        search: Optional search term
        status_filter: Optional status filter - "open" to show only open POs, "closed" for closed, None for all
        has_remaining: Optional filter - if True, only return POs with at least one line that has remaining quantity (qty_received < qty_ordered)
    """
    db = get_db()
    # Search in bons_commande format fields
    query = {}
    if search:
        regex = {"$regex": search, "$options": "i"}
        query = {
            "$or": [
                {"purchase_order_id": regex},
                {"fournisseur.nom": regex},
                {"lignes.description": regex},
            ]
        }
    
    cursor = db["bons_commande"].find(query).sort("date_creation", -1)
    items = []
    async for doc in cursor:
        # Convert to internal format
        internal_po = bons_commande_to_internal_po(doc)
        
        # Filter by status if requested
        if status_filter:
            po_status = internal_po.get("status", "open")
            if status_filter == "open" and po_status == "closed":
                continue
            elif status_filter == "closed" and po_status != "closed":
                continue
        
        # Filter by remaining quantity if requested
        if has_remaining is not None:
            lines = internal_po.get("lines", [])
            has_remaining_qty = any(
                line.get("qty_received", 0) < line.get("qty_ordered", 0)
                for line in lines
            )
            if has_remaining and not has_remaining_qty:
                continue
            elif not has_remaining and has_remaining_qty:
                continue
        
        items.append(serialize_doc(internal_po))
    return items


async def get_purchase_order(po_id: str) -> dict:
    """Return a single PO."""
    db = get_db()
    doc = await db["bons_commande"].find_one({"_id": ObjectId(po_id)})
    if not doc:
        raise ValueError("PO not found.")
    # Convert to internal format
    internal_po = bons_commande_to_internal_po(doc)
    internal_po["status"] = evaluate_po_status(internal_po["lines"])
    # Convert back and update
    bons_commande_doc = internal_po_to_bons_commande(internal_po)
    await db["bons_commande"].update_one(
        {"_id": ObjectId(po_id)}, {"$set": {"status": bons_commande_doc["status"]}}
    )
    return serialize_doc(internal_po)


async def list_po_lines(search: Optional[str] = None) -> list[dict]:
    """Flatten PO lines for quick lookup and optional searching."""
    db = get_db()
    cursor = db["bons_commande"].find().sort("date_creation", -1)
    lookup = (search or "").lower()
    flattened = []
    async for bons_doc in cursor:
        # Convert to internal format
        po = bons_commande_to_internal_po(bons_doc)
        for line in po.get("lines", []):
            entry = {
                "po_number": po["po_number"],
                "supplier": po["supplier"],
                "item_name": line["item_name"],
                "qty_ordered": line["qty_ordered"],
                "qty_received": line["qty_received"],
                "line_id": line["line_id"],
            }
            if lookup:
                if lookup not in entry["item_name"].lower() and lookup not in entry["supplier"].lower():
                    continue
            flattened.append(entry)
    return flattened


def _prepare_updated_lines(
    requested_lines: list[POLineUpdate], existing_lines: list[dict]
) -> list[dict]:
    """Compose persisted PO lines while preserving qty_received."""
    existing_map = {line["line_id"]: line for line in existing_lines}
    new_lines: list[dict] = []
    for idx, requested in enumerate(requested_lines):
        line_id = requested.line_id or str(uuid4())
        existing = existing_map.get(line_id)
        qty_received = existing["qty_received"] if existing else 0
        qty_ordered = requested.qty_ordered
        if qty_received > qty_ordered:
            qty_received = qty_ordered
        status = "closed" if qty_received >= qty_ordered else "open"
        new_lines.append(
            {
                "line_id": line_id,
                "item_name": requested.item_name,
                "qty_ordered": qty_ordered,
                "unit_price": requested.unit_price,
                "qty_received": qty_received,
                "status": status,
            }
        )
    return new_lines


async def update_purchase_order(po_id: str, payload: UpdatePORequest) -> dict:
    """Update the top-level supplier or lines for a PO."""
    db = get_db()
    po_collection = db["bons_commande"]
    bons_doc = await po_collection.find_one({"_id": ObjectId(po_id)})
    if not bons_doc:
        raise ValueError("PO not found.")

    # Convert to internal format
    internal_po = bons_commande_to_internal_po(bons_doc)
    
    update_fields: dict = {}
    if payload.supplier:
        # Update fournisseur object, preserving existing structure
        fournisseur = bons_doc.get("fournisseur", {})
        if not isinstance(fournisseur, dict):
            fournisseur = {}
        fournisseur["nom"] = payload.supplier
        update_fields["fournisseur"] = fournisseur
        # Also update suppliers collection
        await db["suppliers"].update_one(
            {"name": payload.supplier},
            {
                "$set": {
                    "name": payload.supplier,
                    "updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )

    lines_to_use = internal_po["lines"]
    if payload.lines is not None:
        lines_to_use = _prepare_updated_lines(payload.lines, internal_po["lines"])
        # Convert lines back to bons_commande format
        lignes = []
        for line in lines_to_use:
            ligne = {
                "description": line["item_name"],
                "quantite": line["qty_ordered"],
                "prix_unitaire": line["unit_price"],
                "montant_ligne": line.get("montant_ligne", line["qty_ordered"] * line["unit_price"]),
                "unite": line.get("unite", "unité"),
                "numero_ligne": line.get("numero_ligne") or line["line_id"],
                "reference_catalogue": line.get("reference_catalogue", ""),
                "specifications_techniques": line.get("specifications_techniques"),
                "qty_received": line["qty_received"],
                "status": line["status"],
            }
            lignes.append(ligne)
        update_fields["lignes"] = lignes

    update_fields["status"] = evaluate_po_status(lines_to_use)

    updated = await po_collection.find_one_and_update(
        {"_id": ObjectId(po_id)},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise ValueError("PO could not be updated.")
    
    # Return in internal format
    internal_po = bons_commande_to_internal_po(updated)
    return serialize_doc(internal_po)


async def delete_purchase_order(po_id: str) -> dict:
    """Remove a PO and its related GRNs, stock, and disputes."""
    db = get_db()
    po_collection = db["bons_commande"]
    po_doc = await po_collection.find_one({"_id": ObjectId(po_id)})
    if not po_doc:
        raise ValueError("PO not found.")

    grns = db["grns"].find({"po_id": po_id})
    async for grn in grns:
        await db["stock_ledger"].delete_many({"reference": grn["reference"]})
        await db["disputes"].delete_many({"grn_id": str(grn["_id"])})
    await db["grns"].delete_many({"po_id": po_id})
    await po_collection.delete_one({"_id": ObjectId(po_id)})
    await db["disputes"].delete_many({"po_id": po_id})
    return {"deleted": True}

