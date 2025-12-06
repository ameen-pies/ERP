from datetime import datetime
from typing import Optional

from bson import ObjectId
from pymongo import ReturnDocument

from backend.models.supplier_models import SupplierRequest
from backend.utils.database import get_db
from backend.utils.serializers import serialize_doc


async def list_suppliers(search: Optional[str] = None) -> list[dict]:
    """Return suppliers with optional name/id filtering."""
    db = get_db()
    query = {}
    if search:
        regex = {"$regex": search, "$options": "i"}
        query = {"$or": [{"name": regex}, {"id": regex}]}
    cursor = db["suppliers"].find(query).sort("created_at", -1)
    suppliers = []
    async for doc in cursor:
        suppliers.append(serialize_doc(doc))
    return suppliers


async def create_supplier(payload: SupplierRequest) -> dict:
    db = get_db()
    # Generate supplier ID if not provided
    supplier_id = payload.code or f"SUP-{int(datetime.utcnow().timestamp()):X}"
    doc = {
        "id": supplier_id,
        "name": payload.name,
        "tax_id": None,
        "category": None,
        "email": None,
        "phone": None,
        "address": None,
        "status": "ACTIVE",
        "compliance_checked": False,
        "rejection_reason": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db["suppliers"].insert_one(doc)
    created = await db["suppliers"].find_one({"_id": result.inserted_id})
    return serialize_doc(created)


async def update_supplier(supplier_id: str, payload: SupplierRequest) -> dict:
    db = get_db()
    update = {
        "name": payload.name,
        "updated_at": datetime.utcnow(),
    }
    if payload.code:
        update["id"] = payload.code
    updated = await db["suppliers"].find_one_and_update(
        {"_id": ObjectId(supplier_id)},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise ValueError("Supplier not found.")
    return serialize_doc(updated)


async def delete_supplier(supplier_id: str) -> dict:
    db = get_db()
    result = await db["suppliers"].delete_one({"_id": ObjectId(supplier_id)})
    return {"deleted": result.deleted_count > 0}

