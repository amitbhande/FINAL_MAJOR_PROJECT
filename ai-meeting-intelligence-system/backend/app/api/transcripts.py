from __future__ import annotations

from fastapi import APIRouter
from app.models.transcript import (
    MeetingTranscriptCreate,
    MeetingTranscriptListItem,
    MeetingTranscriptOut,
)
from app.repositories.transcripts import list_all_meetings, retrieve_transcript, save_transcript

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("", response_model=MeetingTranscriptOut)
async def upsert_transcript(payload: MeetingTranscriptCreate) -> MeetingTranscriptOut:
    return await save_transcript(payload)


@router.get("/{meeting_id}", response_model=MeetingTranscriptOut)
async def get_transcript(meeting_id: str) -> MeetingTranscriptOut:
    return await retrieve_transcript(meeting_id)


@router.get("", response_model=list[MeetingTranscriptListItem])
async def list_meetings(limit: int = 10000) -> list[MeetingTranscriptListItem]:
    return await list_all_meetings(limit=limit)

