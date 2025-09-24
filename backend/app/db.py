from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from .indexes import ensure_indexes

client: Optional[AsyncIOMotorClient] = None
db = None
submissions = None
reviews = None


async def init_db():
    global client, db, submissions, reviews
    if client is not None:
        return

    client = AsyncIOMotorClient(str(settings.MONGODB_URI))

    _db = client.get_default_database()
    if _db is not None:
        db = _db
    else:
        db = client["ai_code_review"]

    submissions = db["submissions"]
    reviews = db["reviews"]

    await ensure_indexes(db)


async def close_db():
    global client
    if client is not None:
        client.close()
        client = None


def init_db_sync():
    global client, db, submissions, reviews
    if client is not None:
        return
    client = AsyncIOMotorClient(str(settings.MONGODB_URI))
    _db = client.get_default_database()
    db = _db if _db is not None else client["ai_code_review"]
    submissions = db["submissions"]
    reviews = db["reviews"]


def close_db_sync():
    global client
    if client is not None:
        client.close()
        client = None
