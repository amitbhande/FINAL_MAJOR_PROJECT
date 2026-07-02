from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    meeting_id: str
    title: str
    assignee: str | None = None
    due_date: str | None = None
    status: str = "open"


class TaskInDB(BaseModel):
    id: str = Field(alias="_id")
    meeting_id: str
    title: str
    assignee: str | None = None
    due_date: str | None = None
    status: str = "open"
    created_at: datetime


class TaskOut(BaseModel):
    id: str
    meeting_id: str
    title: str
    assignee: str | None = None
    due_date: str | None = None
    status: str
    created_at: datetime

