from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    title: str
    owner: str | None = None
    due_date: str | None = None
    status: str = "open"


class MeetingCreate(BaseModel):
    title: str | None = None
    participants: list[str] = Field(default_factory=list)


class MeetingInDB(BaseModel):
    id: str = Field(alias="_id")
    title: str | None = None
    participants: list[str] = Field(default_factory=list)
    audio_filename: str | None = None
    transcript_text: str
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    sentiment: dict[str, Any] | None = None
    action_items: list[ActionItem] = Field(default_factory=list)
    created_at: datetime


class MeetingOut(BaseModel):
    id: str
    title: str | None = None
    participants: list[str]
    audio_filename: str | None = None
    transcript_text: str
    speaker_segments: list[dict[str, Any]] = Field(default_factory=list)
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    sentiment: dict[str, Any] | None = None
    action_items: list[ActionItem]
    created_at: datetime


class MeetingListItem(BaseModel):
    id: str
    title: str | None = None
    participants: list[str]
    created_at: datetime


class AskRequest(BaseModel):
    question: str
    top_k: int = 6


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)

