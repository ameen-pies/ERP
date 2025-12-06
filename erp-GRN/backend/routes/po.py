from fastapi import APIRouter, HTTPException

from backend.models.po_models import AddPOLineRequest, CreatePORequest, UpdatePORequest
from backend.services.po_service import (
    add_line_to_po,
    create_purchase_order,
    delete_purchase_order,
    get_purchase_order,
    list_purchase_orders,
    update_purchase_order,
)

router = APIRouter(prefix="/api")


@router.post("/po", status_code=201)
async def create_po(payload: CreatePORequest) -> dict:
    try:
        return await create_purchase_order(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/po/{po_id}/lines", status_code=201)
async def add_po_line(po_id: str, payload: AddPOLineRequest) -> dict:
    try:
        return await add_line_to_po(po_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/po")
async def get_po_list(
    search: str | None = None, 
    status: str | None = None,
    has_remaining: bool | None = None
) -> list[dict]:
    return await list_purchase_orders(search, status_filter=status, has_remaining=has_remaining)


@router.get("/po/{po_id}")
async def get_po(po_id: str) -> dict:
    try:
        return await get_purchase_order(po_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/po/{po_id}")
async def modify_po(po_id: str, payload: UpdatePORequest) -> dict:
    try:
        return await update_purchase_order(po_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/po/{po_id}")
async def purge_po(po_id: str) -> dict:
    try:
        return await delete_purchase_order(po_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

