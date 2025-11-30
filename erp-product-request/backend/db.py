from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

# Initialize connection
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print(f"✓ Connected to MongoDB: {MONGO_DB_NAME}")
except ConnectionFailure as e:
    print(f"✗ MongoDB connection failed: {e}")
    raise

# Get database and collection
db = client[MONGO_DB_NAME]
pr_collection = db["purchase_requests"]

# Create indexes for better performance
try:
    pr_collection.create_index("id", unique=True)
    pr_collection.create_index("statut")
    pr_collection.create_index("demandeur")
    pr_collection.create_index("date_creation")
    print("✓ Database indexes created")
except Exception as e:
    print(f"⚠ Index creation warning: {e}")

def get_pr_collection():
    """Return the PR collection for database operations"""
    return pr_collection

def get_database():
    """Return the database instance"""
    return db

def test_connection():
    """Test MongoDB connection"""
    try:
        client.admin.command('ping')
        return True
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False