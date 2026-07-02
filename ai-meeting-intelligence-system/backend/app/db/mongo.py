from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


class Mongo:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongo = Mongo()


async def connect_mongo() -> None:
    mongo.client = AsyncIOMotorClient(settings.mongodb_uri)
    mongo.db = mongo.client[settings.mongodb_db]
    await mongo.db.meetings.create_index("created_at")
    await mongo.db.tasks.create_index("meeting_id")
    await mongo.db.tasks.create_index([("assignee", 1), ("status", 1)])
    await mongo.db.meeting_transcripts.create_index("created_at")
    await mongo.db.meeting_transcripts.create_index("meeting_id", unique=True)
    await mongo.db.task_tracker.create_index("task_id", unique=True)
    await mongo.db.task_tracker.create_index([("meeting_id", 1), ("status", 1)])
    await mongo.db.user_logins.create_index("logged_in_at")
    await mongo.db.user_logins.create_index("email")


async def disconnect_mongo() -> None:
    if mongo.client is not None:
        mongo.client.close()
    mongo.client = None
    mongo.db = None

