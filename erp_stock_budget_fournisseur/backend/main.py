"""
Application FastAPI principale avec MongoDB
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import init_db
from backend.routes_suppliers import router as suppliers_router
from backend.routes_budget import router as budget_router
from backend.routes_stock import router as stock_router

# Initialisation de la base de données
init_db()

app = FastAPI(
    title="ERP Core API - MongoDB Edition",
    description="API pour Gestion Fournisseurs, Budget et Stock avec MongoDB",
    version="4.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes
app.include_router(suppliers_router)
app.include_router(budget_router)
app.include_router(stock_router)

@app.get("/")
def root():
    """Endpoint racine"""
    return {
        "message": "ERP Core API - MongoDB Edition",
        "version": "4.0.0",
        "status": "operational",
        "database": "MongoDB",
        "endpoints": {
            "suppliers": "/suppliers",
            "budget": "/budget",
            "stock": "/stock",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API et de MongoDB"""
    try:
        from config.database import get_database
        db = get_database()
        # Test de connexion MongoDB
        await db.command("ping")
        
        return {
            "status": "healthy",
            "api": "operational",
            "database": "connected",
            "mongodb": "operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "api": "operational",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/stats")
async def get_statistics():
    """Statistiques globales du système"""
    from config.database import get_database
    db = get_database()
    
    try:
        suppliers_count = await db.suppliers.count_documents({})
        budgets_count = await db.budgets.count_documents({})
        stock_items_count = await db.stock.count_documents({})
        movements_count = await db.stock_movements.count_documents({})
        
        return {
            "suppliers": suppliers_count,
            "budgets": budgets_count,
            "stock_items": stock_items_count,
            "stock_movements": movements_count
        }
    except Exception as e:
        return {
            "error": str(e)
        }
