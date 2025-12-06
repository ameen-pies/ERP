from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = (
    "mongodb+srv://medhelaliamin125_db_user:aUfXpfkyHbpynyKL"
    "@erp.yrgvgdj.mongodb.net/?retryWrites=true&w=majority"
)


class MongoDB:
    """Singleton holder for the Mongo client and database reference."""

    client: AsyncIOMotorClient | None = None
    db = None


async def connect_to_mongo():
    """Establish a connection to MongoDB and store the database handle."""
    if MongoDB.client is None:
        MongoDB.client = AsyncIOMotorClient(MONGO_URI)
        MongoDB.db = MongoDB.client["purchase_request"]
        # Ping to ensure the connection is live.
        await MongoDB.db.command("ping")


async def close_mongo_connection():
    """Gracefully close the MongoDB connection."""
    if MongoDB.client is not None:
        MongoDB.client.close()
        MongoDB.client = None
        MongoDB.db = None


def get_db():
    """Return the connected database instance."""
    if MongoDB.db is None:
        raise RuntimeError("MongoDB is not connected yet.")
    return MongoDB.db

