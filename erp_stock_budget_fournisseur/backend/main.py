"""
Application FastAPI principale avec MongoDB
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import init_db
from backend.routes_departments import router as departments_router
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
app.include_router(departments_router)
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
        departments_count = await db.departments.count_documents({})
        
        # Calculer la valeur totale du stock
        stock_items = await db.stock.find({}).to_list(length=None)
        total_stock_value = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in stock_items)
        total_stock_qty = sum(item.get("quantity", 0) for item in stock_items)
        
        # Articles en stock faible
        low_stock_count = sum(1 for item in stock_items if item.get("quantity", 0) < item.get("min_threshold", 0))
        
        # Fournisseurs actifs
        active_suppliers = await db.suppliers.count_documents({"status": "ACTIVE"})
        
        return {
            "suppliers": suppliers_count,
            "suppliers_active": active_suppliers,
            "budgets": budgets_count,
            "departments": departments_count,
            "stock_items": stock_items_count,
            "stock_movements": movements_count,
            "total_stock_value": total_stock_value,
            "total_stock_quantity": total_stock_qty,
            "low_stock_items": low_stock_count
        }
    except Exception as e:
        return {
            "error": str(e)
        }
