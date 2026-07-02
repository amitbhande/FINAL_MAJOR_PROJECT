from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.api.transcribe import _stream_to_disk, _validate_extension
from app.core.config import settings
from app.db.mongo import mongo
from app.models.meeting import AskRequest, AskResponse, MeetingListItem, MeetingOut
from app.models.task import TaskOut
from fastapi.concurrency import run_in_threadpool
from app.services.llm import (
    extract_action_items,
    extract_key_points,
    heuristic_key_points_from_transcript,
    heuristic_summary_fallback,
    rag_answer,
    summarize,
)
from app.services.sentiment import simple_sentiment
from app.services.transcription import transcriber
from app.services.vector_store import query as vs_query
from app.services.vector_store import upsert_transcript
from app.utils.ids import oid, oid_str

router = APIRouter(prefix="/meetings", tags=["meetings"])
logger = logging.getLogger(__name__)


@router.post("", response_model=MeetingOut)
async def upload_meeting(
    audio: UploadFile = File(...),
    title: str | None = Form(default=None),
    participants: str | None = Form(default=None),
) -> MeetingOut:
    try:
        if mongo.db is None:
            raise RuntimeError("Mongo not initialized")

        # Save upload to disk in chunks (avoids full in-memory buffering for large files).
        uploads_dir = Path(settings.uploads_dir).resolve()
        uploads_dir.mkdir(parents=True, exist_ok=True)

        ext = _validate_extension(audio)
        file_id = uuid4().hex
        original_path = uploads_dir / f"{file_id}{ext}"

        try:
            await _stream_to_disk(audio, original_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}") from e

        participants_list = _parse_csv(participants)
        tr = await run_in_threadpool(transcriber.transcribe_meeting_upload_path, original_path, participants_list)
        transcript = tr.transcript_text
        if not transcript:
            raise HTTPException(status_code=400, detail="Failed to transcribe audio")

        llm_text = tr.labeled_transcript or transcript
        speaker_attr = bool(tr.speaker_segments)

        created_at = datetime.now(timezone.utc)
        meeting_doc: dict[str, Any] = {
            "title": title or (audio.filename or "Untitled meeting"),
            "participants": participants_list,
            "audio_filename": audio.filename,
            "transcript_text": transcript,
            "speaker_segments": tr.speaker_segments or [],
            "summary": None,
            "key_points": [],
            "sentiment": simple_sentiment(transcript),
            "action_items": [],
            "created_at": created_at,
        }
        ins = await mongo.db.meetings.insert_one(meeting_doc)
        meeting_id = oid_str(ins.inserted_id)

        try:
            chunks = upsert_transcript(meeting_id, llm_text)
        except Exception:
            chunks = 0

        try:
            meeting_doc["summary"] = await summarize(llm_text, speaker_attributed=speaker_attr)
            meeting_doc["key_points"] = await extract_key_points(
                llm_text, speaker_attributed=speaker_attr
            )
            items = await extract_action_items(llm_text, speaker_attributed=speaker_attr)
        except Exception:
            logger.exception(
                "LLM insights failed — using transcript fallbacks (check GEMINI_API_KEY / LLM_API_KEY)"
            )
            meeting_doc["summary"] = heuristic_summary_fallback(llm_text)
            meeting_doc["key_points"] = []
            items = []
        if not (meeting_doc.get("summary") or "").strip():
            meeting_doc["summary"] = heuristic_summary_fallback(llm_text)
        if not meeting_doc.get("key_points"):
            meeting_doc["key_points"] = heuristic_key_points_from_transcript(llm_text)

        meeting_doc["action_items"] = [
            {
                "title": (x.get("title") or "").strip(),
                "owner": x.get("owner"),
                "due_date": x.get("due_date"),
                "status": "open",
            }
            for x in items
            if (x.get("title") or "").strip()
        ]

        await mongo.db.meetings.update_one(
            {"_id": oid(meeting_id)},
            {
                "$set": {
                    "summary": meeting_doc["summary"],
                    "key_points": meeting_doc["key_points"],
                    "action_items": meeting_doc["action_items"],
                }
            },
        )

        await mongo.db.meeting_transcripts.update_one(
            {"meeting_id": meeting_id},
            {
                "$set": {
                    "meeting_id": meeting_id,
                    "meeting_title": meeting_doc["title"],
                    "participants": participants_list,
                    "speaker_segments": tr.speaker_segments or [],
                    "transcript": transcript,
                    "summary": meeting_doc["summary"],
                    "sentiment": meeting_doc["sentiment"],
                    "created_at": created_at,
                }
            },
            upsert=True,
        )

        if meeting_doc["action_items"]:
            await mongo.db.tasks.insert_many(
                [
                    {
                        "meeting_id": meeting_id,
                        "title": ai["title"],
                        "assignee": ai.get("owner"),
                        "due_date": ai.get("due_date"),
                        "status": "open",
                        "created_at": created_at,
                    }
                    for ai in meeting_doc["action_items"]
                ]
            )
            await mongo.db.task_tracker.insert_many(
                [
                    {
                        "task_id": uuid4().hex,
                        "task_name": ai["title"],
                        "assigned_to": ai.get("owner"),
                        "meeting_id": meeting_id,
                        "deadline": ai.get("due_date"),
                        "status": "pending",
                        "created_at": created_at,
                        "updated_at": created_at,
                    }
                    for ai in meeting_doc["action_items"]
                ]
            )

        return MeetingOut(
            id=meeting_id,
            title=meeting_doc["title"],
            participants=participants_list,
            audio_filename=meeting_doc["audio_filename"],
            transcript_text=transcript,
            speaker_segments=tr.speaker_segments or [],
            summary=meeting_doc["summary"],
            key_points=meeting_doc["key_points"],
            sentiment=meeting_doc["sentiment"],
            action_items=meeting_doc["action_items"],
            created_at=created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload meeting failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", response_model=list[MeetingListItem])
async def list_meetings(limit: int = 10000) -> list[MeetingListItem]:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")
    cur = mongo.db.meetings.find({}, {"title": 1, "participants": 1, "created_at": 1}).sort("created_at", -1).limit(min(limit, 10000))
    out: list[MeetingListItem] = []
    async for doc in cur:
        out.append(
            MeetingListItem(
                id=oid_str(doc["_id"]),
                title=doc.get("title"),
                participants=doc.get("participants", []),
                created_at=doc.get("created_at"),
            )
        )
    return out


@router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(meeting_id: str) -> MeetingOut:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")
    doc = await mongo.db.meetings.find_one({"_id": oid(meeting_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingOut(
        id=oid_str(doc["_id"]),
        title=doc.get("title"),
        participants=doc.get("participants", []),
        audio_filename=doc.get("audio_filename"),
        transcript_text=doc.get("transcript_text", ""),
        speaker_segments=doc.get("speaker_segments") or [],
        summary=doc.get("summary"),
        key_points=doc.get("key_points", []),
        sentiment=doc.get("sentiment"),
        action_items=doc.get("action_items", []),
        created_at=doc.get("created_at"),
    )


@router.get("/{meeting_id}/tasks", response_model=list[TaskOut])
async def get_meeting_tasks(meeting_id: str) -> list[TaskOut]:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")
    cur = mongo.db.tasks.find({"meeting_id": meeting_id}).sort("created_at", -1)
    out: list[TaskOut] = []
    async for doc in cur:
        out.append(
            TaskOut(
                id=oid_str(doc["_id"]),
                meeting_id=doc["meeting_id"],
                title=doc["title"],
                assignee=doc.get("assignee"),
                due_date=doc.get("due_date"),
                status=doc.get("status", "open"),
                created_at=doc.get("created_at"),
            )
        )
    return out


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    chunks = vs_query(req.question, top_k=req.top_k)
    try:
        answer = await rag_answer(req.question, chunks)
    except Exception as e:
        logger.exception("RAG /meetings/ask LLM step failed")
        answer = (
            "Could not generate an answer — the LLM request failed. "
            "Check GEMINI_API_KEY / LLM_API_KEY in backend .env and try again. "
            f"({type(e).__name__}: {e})"
        )
    return AskResponse(answer=answer, sources=chunks)


def _parse_csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def _safe_suffix(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ".mp3"
    suf = "." + filename.split(".")[-1].lower()
    if suf in {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".webm", ".mp4", ".mov", ".mkv"}:
        return suf
    return ".mp3"

