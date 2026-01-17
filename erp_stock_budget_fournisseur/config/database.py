"""
Configuration et connexion MongoDB avec Motor (async)
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection URI
MONGO_URI = os.getenv(
    "MONGO_URI"
)

# Database name
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Global client and database instances
client: Optional[AsyncIOMotorClient] = None
database = None
sync_client: Optional[MongoClient] = None

def get_database():
    """Get MongoDB database instance"""
    global database
    if database is None:
        global client
        client = AsyncIOMotorClient(MONGO_URI)
        database = client[DATABASE_NAME]
    return database

def get_sync_client():
    """Get synchronous MongoDB client for initialization"""
    global sync_client
    if sync_client is None:
        sync_client = MongoClient(MONGO_URI)
    return sync_client

def get_sync_database():
    """Get synchronous database instance for initialization"""
    sync_db = get_sync_client()[DATABASE_NAME]
    return sync_db

async def close_database():
    """Close MongoDB connection"""
    global client, sync_client
    if client:
        client.close()
    if sync_client:
        sync_client.close()

def init_db():
    """Initialisation de la base de données MongoDB et création des index"""
    db = get_sync_database()
    
    # Create indexes for better performance
    try:
        # Departments collection indexes
        db.departments.create_index("code", unique=True)
        db.departments.create_index("status")
        
        # Suppliers collection indexes
        db.suppliers.create_index("tax_id", unique=True)
        db.suppliers.create_index("status")
        
        # Budgets collection indexes
        db.budgets.create_index("department", unique=True)
        
        # Budget transactions indexes
        db.budget_transactions.create_index("department")
        db.budget_transactions.create_index("created_at")
        
        # Pending transactions indexes
        db.pending_transactions.create_index("department")
        db.pending_transactions.create_index("status")
        
        # Stock items indexes
        db.stock.create_index("item_id", unique=True)
        
        # Stock movements indexes
        db.stock_movements.create_index("item_id")
        db.stock_movements.create_index("created_at")
        
        # Accounting journal indexes
        db.accounting_journal.create_index("date")
        
        # Projects indexes
        db.projects.create_index("project_id", unique=True)
        
        print(f"[OK] Base de donnees MongoDB '{DATABASE_NAME}' (purchase_request) initialisee avec succes")
    except Exception as e:
        print(f"[WARNING] Erreur lors de l'initialisation: {e}")
