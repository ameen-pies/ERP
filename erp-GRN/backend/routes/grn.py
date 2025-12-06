from fastapi import APIRouter, HTTPException

from backend.models.grn_models import CreateGRNRequest, UpdateGRNRequest
from backend.services.grn_service import (
    create_grn,
    delete_grn,
    list_grns,
    update_grn,
)

router = APIRouter(prefix="/api")


@router.post("/grn", status_code=201)
async def submit_grn(payload: CreateGRNRequest) -> dict:
    try:
        return await create_grn(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/grn")
async def get_grns(search: str | None = None) -> list[dict]:
    return await list_grns(search)


@router.put("/grn/{grn_id}")
async def modify_grn(grn_id: str, payload: UpdateGRNRequest) -> dict:
    try:
        return await update_grn(grn_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/grn/{grn_id}")
async def purge_grn(grn_id: str) -> dict:
    try:
        return await delete_grn(grn_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

