from backend.utils.database import get_db
from backend.utils.serializers import serialize_doc


async def get_dashboard_overview() -> list[dict]:
    """Return collection metadata for the Streamlit dashboard."""
    db = get_db()
    collections = await db.list_collection_names()
    overview = []
    for name in sorted(collections):
        collection = db[name]
        count = await collection.count_documents({})
        sample = await collection.find_one({})
        overview.append(
            {
                "name": name,
                "count": count,
                "sample": serialize_doc(sample) if sample else None,
            }
        )
    return overview


async def clear_demo_collections() -> None:
    """Empty collections that are used by the GRN demo."""
    db = get_db()
    demo_collections = [
        "bons_commande",
        "grns",
        "stock_ledger",
        "disputes",
        "suppliers",
        "items",
    ]
    for coll_name in demo_collections:
        await db[coll_name].delete_many({})

