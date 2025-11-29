# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: Optional[AsyncIOMotorClient] = None

database = Database()

async def get_database():
    db_name = os.getenv("DATABASE_NAME", "erp_db")
    if not database.client:
        raise Exception("Database client is not connected")
    return database.client[db_name]

async def connect_to_mongo():
    mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        raise Exception("❌ MONGODB_URL not found in .env file")
    database.client = AsyncIOMotorClient(mongo_url)
    try:
        # motor/async ping; this is not truly async but Atlas accepts command
        await database.client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        raise

async def close_mongo_connection():
    if database.client:
        database.client.close()
        print("❌ Closed MongoDB connection")
