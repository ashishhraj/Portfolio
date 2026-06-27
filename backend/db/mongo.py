from motor.motor_asyncio import AsyncIOMotorClient
import os, logging

logger = logging.getLogger(__name__)
client = None
db = None

async def init_mongo():
    global client, db
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME   = os.getenv("DB_NAME", "portfolio")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    # Create indexes
    await db.projects.create_index("slug", unique=True)
    await db.certifications.create_index("title")
    await db.resume.create_index("updated_at")
    logger.info(f"✅ MongoDB connected: {DB_NAME}")

def get_db():
    return db
