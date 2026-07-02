from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.db.mongo import mongo
from app.models.transcript import (
    MeetingTranscriptCreate,
    MeetingTranscriptListItem,
    MeetingTranscriptOut,
)
from app.utils.ids import oid_str


COLL = "meeting_transcripts"


async def save_transcript(payload: MeetingTranscriptCreate) -> MeetingTranscriptOut:
    """
    Upsert a meeting transcript by meeting_id.
    """
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    now = datetime.now(timezone.utc)
    doc = {
        "meeting_id": payload.meeting_id,
        "meeting_title": payload.meeting_title,
        "participants": payload.participants,
        "speaker_segments": payload.speaker_segments,
        "transcript": payload.transcript,
        "summary": payload.summary,
        "sentiment": payload.sentiment,
        "created_at": now,
    }

    await mongo.db[COLL].update_one({"meeting_id": payload.meeting_id}, {"$set": doc}, upsert=True)
    saved = await mongo.db[COLL].find_one({"meeting_id": payload.meeting_id})
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save transcript")

    return MeetingTranscriptOut(
        id=oid_str(saved["_id"]),
        meeting_id=saved["meeting_id"],
        meeting_title=saved.get("meeting_title"),
        participants=saved.get("participants") or [],
        speaker_segments=saved.get("speaker_segments") or [],
        transcript=saved.get("transcript", ""),
        summary=saved.get("summary"),
        sentiment=saved.get("sentiment"),
        created_at=saved.get("created_at", now),
    )


async def retrieve_transcript(meeting_id: str) -> MeetingTranscriptOut:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    doc = await mongo.db[COLL].find_one({"meeting_id": meeting_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return MeetingTranscriptOut(
        id=oid_str(doc["_id"]),
        meeting_id=doc["meeting_id"],
        meeting_title=doc.get("meeting_title"),
        participants=doc.get("participants") or [],
        speaker_segments=doc.get("speaker_segments") or [],
        transcript=doc.get("transcript", ""),
        summary=doc.get("summary"),
        sentiment=doc.get("sentiment"),
        created_at=doc.get("created_at"),
    )


async def list_all_meetings(limit: int = 100) -> list[MeetingTranscriptListItem]:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    cur = (
        mongo.db[COLL]
        .find({}, {"meeting_id": 1, "meeting_title": 1, "created_at": 1})
        .sort("created_at", -1)
        .limit(min(limit, 10000))
    )

    out: list[MeetingTranscriptListItem] = []
    async for doc in cur:
        out.append(
            MeetingTranscriptListItem(
                meeting_id=doc.get("meeting_id"),
                meeting_title=doc.get("meeting_title"),
                created_at=doc.get("created_at"),
            )
        )
    return out

