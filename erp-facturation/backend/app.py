from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
from facture_api import facture_router
from db import test_connection
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Module d'achat - Invoice Management",
    description="API pour la gestion des factures avec OCR et validation PO",
    version="1.0.0"
)

print("=" * 50)
print("🚀 FastAPI Application Starting...")
print("=" * 50)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(facture_router)

@app.get("/")
def root():
    return {
        "message": "Module d'achat - Invoice Management",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "upload_facture": "POST /factures/upload-and-validate",
            "list_factures": "GET /factures/",
            "get_facture": "GET /factures/{facture_id}",
            "approve_facture": "POST /factures/{facture_id}/approve",
            "reject_facture": "POST /factures/{facture_id}/reject",
            "mark_paid": "POST /factures/{facture_id}/mark-paid",
            "stats": "GET /factures/stats/summary"
        }
    }

@app.get("/health")
def health_check():
    db_status = test_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "api_version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("✅ FastAPI app started successfully")
    logger.info("📄 Facture Management API")
    logger.info("🔍 Available routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            logger.info(f"   {methods[0]:6} {route.path}")
    logger.info("=" * 50)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 FastAPI app shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)