from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "purchase_request")

# Initialize connection
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print(f"✅ Connected to MongoDB: {MONGO_DB_NAME}")
except ConnectionFailure as e:
    print(f"❌ MongoDB connection failed: {e}")
    raise

# Get database
db = client[MONGO_DB_NAME]

# Collections - FIXED: Use correct collection name
pr_collection = db["purchase_requests"]
po_collection = db["bons_commande"]  # ✅ CHANGED FROM "POs" to "bons_commande"
facture_collection = db["factures"]

# Create indexes for better performance
try:
    # PR indexes
    pr_collection.create_index("id", unique=True)
    pr_collection.create_index("statut")
    pr_collection.create_index("demandeur")
    pr_collection.create_index("date_creation")
    
    # PO indexes - FIXED: Use correct field name
    po_collection.create_index("purchase_order_id", unique=True)
    po_collection.create_index("linked_pr_id")
    po_collection.create_index("status")
    
    # Facture indexes
    facture_collection.create_index("facture_id", unique=True)
    facture_collection.create_index("linked_po_id")
    facture_collection.create_index("status")
    facture_collection.create_index("date_reception")
    
    print("✅ Database indexes created")
except Exception as e:
    print(f"⚠️ Index creation warning: {e}")

def get_pr_collection():
    return pr_collection

def get_po_collection():
    return po_collection

def get_facture_collection():
    return facture_collection

def get_database():
    return db

def test_connection():
    try:
        client.admin.command('ping')
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False