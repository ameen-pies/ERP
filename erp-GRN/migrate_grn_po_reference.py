"""
Migration script to add po_reference to existing GRN documents.

This script:
1. Finds all GRNs that don't have po_reference or have it as "N/A"
2. Looks up the PO using the po_id
3. Updates the GRN document with the correct po_reference

Run this script once to migrate existing GRN data.
"""

import asyncio
from bson import ObjectId

from backend.utils.database import get_db, connect_to_mongo, close_mongo_connection
from backend.utils.po_adapter import bons_commande_to_internal_po


async def migrate_grn_po_references():
    """Migrate existing GRNs to include po_reference field."""
    await connect_to_mongo()
    db = get_db()
    
    grn_collection = db["grns"]
    po_collection = db["bons_commande"]
    
    # Find all GRNs
    cursor = grn_collection.find({})
    total_grns = 0
    updated_count = 0
    error_count = 0
    
    print("Starting GRN migration...")
    print("=" * 50)
    
    async for grn in cursor:
        total_grns += 1
        grn_id = grn.get("_id")
        grn_reference = grn.get("reference", "Unknown")
        po_id = grn.get("po_id")
        current_po_reference = grn.get("po_reference")
        
        # Skip if po_reference already exists and is valid
        if current_po_reference and current_po_reference != "N/A":
            print(f"✓ GRN {grn_reference} already has po_reference: {current_po_reference}")
            continue
        
        if not po_id:
            print(f"⚠ GRN {grn_reference} has no po_id, skipping...")
            error_count += 1
            continue
        
        try:
            # Look up the PO
            po_doc = await po_collection.find_one({"_id": ObjectId(po_id)})
            if not po_doc:
                print(f"⚠ GRN {grn_reference}: PO {po_id} not found, skipping...")
                error_count += 1
                continue
            
            # Convert to internal format to get po_number
            po_doc_internal = bons_commande_to_internal_po(po_doc)
            po_reference = po_doc_internal.get("po_number", "N/A")
            
            # Update the GRN document
            result = await grn_collection.update_one(
                {"_id": grn_id},
                {"$set": {"po_reference": po_reference}}
            )
            
            if result.modified_count > 0:
                print(f"✓ Updated GRN {grn_reference}: po_reference = {po_reference}")
                updated_count += 1
            else:
                print(f"⚠ GRN {grn_reference}: No update needed (already set to {po_reference})")
                
        except Exception as e:
            print(f"✗ Error updating GRN {grn_reference}: {e}")
            error_count += 1
    
    print("=" * 50)
    print(f"Migration complete!")
    print(f"Total GRNs processed: {total_grns}")
    print(f"Successfully updated: {updated_count}")
    print(f"Errors/Skipped: {error_count}")
    
    await close_mongo_connection()


if __name__ == "__main__":
    print("GRN PO Reference Migration Script")
    print("This script will add po_reference to existing GRN documents.")
    print()
    
    try:
        asyncio.run(migrate_grn_po_references())
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user.")
    except Exception as e:
        print(f"\n\nMigration failed with error: {e}")
        import traceback
        traceback.print_exc()

