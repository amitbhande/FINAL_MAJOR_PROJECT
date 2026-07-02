from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from app.db.mongo import mongo

router = APIRouter(prefix="/auth", tags=["auth"])


class LogLoginRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    source: str = "login"  # "login" or "register"


@router.post("/log-login")
async def log_login(req: LogLoginRequest) -> dict:
    """
    Record a user login event in MongoDB.
    Called when a user successfully logs in or registers.
    """
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    doc = {
        "email": req.email,
        "name": req.name,
        "source": req.source,
        "logged_in_at": datetime.now(timezone.utc),
    }
    await mongo.db.user_logins.insert_one(doc)
    return {"ok": True}
