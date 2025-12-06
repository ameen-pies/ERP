from fastapi import APIRouter, HTTPException

from backend.models.supplier_models import SupplierRequest
from backend.services.supplier_service import (
    create_supplier,
    delete_supplier,
    list_suppliers,
    update_supplier,
)

router = APIRouter(prefix="/api")


@router.get("/suppliers")
async def get_suppliers(search: str | None = None) -> list[dict]:
    return await list_suppliers(search)


@router.post("/suppliers", status_code=201)
async def add_supplier(payload: SupplierRequest) -> dict:
    return await create_supplier(payload)


@router.put("/suppliers/{supplier_id}")
async def modify_supplier(
    supplier_id: str, payload: SupplierRequest
) -> dict:
    try:
        return await update_supplier(supplier_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/suppliers/{supplier_id}")
async def remove_supplier(supplier_id: str) -> dict:
    try:
        return await delete_supplier(supplier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

