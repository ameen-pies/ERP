from fastapi import APIRouter

from backend.services.stock_service import get_stock_ledger_by_grn, list_stock_ledger

router = APIRouter(prefix="/api")


@router.get("/stock")
async def stock_ledger(search: str | None = None) -> list[dict]:
    return await list_stock_ledger(search)


@router.get("/stock/by-grn")
async def stock_ledger_by_grn() -> dict:
    return await get_stock_ledger_by_grn()

