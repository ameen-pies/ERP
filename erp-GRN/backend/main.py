from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.dashboard import router as dashboard_router
from backend.routes.disputes import router as disputes_router
from backend.routes.grn import router as grn_router
from backend.routes.po import router as po_router
from backend.routes.po_lines import router as po_lines_router
from backend.routes.stock import router as stock_router
from backend.routes.suppliers import router as suppliers_router
from backend.services.seed_service import seed_all
from backend.utils.database import close_mongo_connection, connect_to_mongo

app = FastAPI(title="Mini ERP GRN Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(po_router)
app.include_router(grn_router)
app.include_router(stock_router)
app.include_router(disputes_router)
app.include_router(dashboard_router)
app.include_router(po_lines_router)
app.include_router(suppliers_router)


@app.on_event("startup")
async def on_startup():
    await connect_to_mongo()
    await seed_all()


@app.on_event("shutdown")
async def on_shutdown():
    await close_mongo_connection()

