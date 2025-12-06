from fastapi import APIRouter

from backend.services.po_service import list_po_lines

router = APIRouter(prefix="/api")


@router.get("/po-lines")
async def get_po_lines(search: str | None = None) -> list[dict]:
    return await list_po_lines(search)

