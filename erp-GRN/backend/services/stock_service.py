from datetime import datetime
from typing import Optional

from backend.utils.database import get_db
from backend.utils.serializers import serialize_doc


async def record_stock_movement(
    item_name: str, qty: int, reference: str, movement_type: str = "GRN"
) -> dict:
    """Create a ledger entry when goods are accepted."""
    if qty <= 0:
        return {}

    db = get_db()
    doc = {
        "item_name": item_name,
        "qty": qty,
        "movement_type": movement_type,
        "reference": reference,
        "created_at": datetime.utcnow(),
    }
    result = await db["stock_ledger"].insert_one(doc)
    entry = await db["stock_ledger"].find_one({"_id": result.inserted_id})
    return serialize_doc(entry)


async def list_stock_ledger(search: Optional[str] = None) -> list[dict]:
    """Return stock movements sorted by most recent, with optional search."""
    db = get_db()
    query = {}
    if search:
        regex = {"$regex": search, "$options": "i"}
        query = {
            "$or": [
                {"item_name": regex},
                {"reference": regex},
                {"movement_type": regex},
            ]
        }
    cursor = db["stock_ledger"].find(query).sort("created_at", -1)
    ledger = []
    async for entry in cursor:
        ledger.append(serialize_doc(entry))
    return ledger


async def get_stock_ledger_by_grn() -> dict:
    """Return stock ledger grouped by GRN reference (only passed GRNs)."""
    db = get_db()
    cursor = db["stock_ledger"].find().sort("created_at", -1)
    
    # Group by GRN reference
    grn_groups = {}
    async for entry in cursor:
        ref = entry.get("reference", "Unknown")
        if ref not in grn_groups:
            grn_groups[ref] = {
                "grn_reference": ref,
                "items": [],
                "total_qty": 0,
                "created_at": entry.get("created_at"),
            }
        
        grn_groups[ref]["items"].append({
            "item_name": entry.get("item_name"),
            "qty": entry.get("qty", 0),
            "movement_type": entry.get("movement_type", "GRN"),
            "created_at": entry.get("created_at"),
        })
        grn_groups[ref]["total_qty"] += entry.get("qty", 0)
    
    # Convert to list and serialize
    result = []
    for grn_data in grn_groups.values():
        result.append(grn_data)
    
    return {"grouped_by_grn": result, "total_grns": len(result)}

