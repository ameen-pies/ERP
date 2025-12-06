from fastapi import APIRouter

from backend.services.dashboard_service import (
    clear_demo_collections,
    get_dashboard_overview,
)
from backend.services.seed_service import seed_all

router = APIRouter(prefix="/api")


@router.get("/dashboard/overview")
async def dashboard_overview() -> list[dict]:
    return await get_dashboard_overview()


@router.post("/dashboard/clear-demo")
async def clear_demo_data() -> dict:
    await clear_demo_collections()
    await seed_all()
    return {"status": "demo data reset"}

