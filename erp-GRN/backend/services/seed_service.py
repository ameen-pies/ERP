from datetime import datetime

from backend.utils.database import get_db


async def ensure_collections_exist():
    """Ensure all required collections exist in the database."""
    db = get_db()
    
    # Collections that should exist:
    # - bons_commande (already exists with data)
    # - suppliers (already exists with data)
    # - grns (may need to be created)
    # - stock_ledger (may need to be created)
    # - disputes (may need to be created)
    
    # Create collections by inserting and deleting a dummy document if they don't exist
    collections_to_ensure = ["grns", "stock_ledger", "disputes"]
    
    for collection_name in collections_to_ensure:
        collection = db[collection_name]
        # Check if collection exists by trying to count documents
        try:
            await collection.count_documents({})
        except Exception:
            # Collection doesn't exist, create it by inserting a dummy doc
            await collection.insert_one({"_temp": True})
            await collection.delete_one({"_temp": True})


async def seed_all():
    """Ensure all required collections exist."""
    await ensure_collections_exist()

