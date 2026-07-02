from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MeetingTranscriptBase(BaseModel):
    meeting_id: str
    meeting_title: str | None = None
    participants: list[str] = Field(default_factory=list)
    speaker_segments: list[dict[str, Any]] = Field(default_factory=list)
    transcript: str
    summary: str | None = None
    sentiment: dict[str, Any] | None = None
    created_at: datetime


class MeetingTranscriptCreate(BaseModel):
    meeting_id: str
    meeting_title: str | None = None
    participants: list[str] = Field(default_factory=list)
    speaker_segments: list[dict[str, Any]] = Field(default_factory=list)
    transcript: str
    summary: str | None = None
    sentiment: dict[str, Any] | None = None


class MeetingTranscriptInDB(MeetingTranscriptBase):
    id: str = Field(alias="_id")


class MeetingTranscriptOut(MeetingTranscriptBase):
    id: str


class MeetingTranscriptListItem(BaseModel):
    meeting_id: str
    meeting_title: str | None = None
    created_at: datetime

