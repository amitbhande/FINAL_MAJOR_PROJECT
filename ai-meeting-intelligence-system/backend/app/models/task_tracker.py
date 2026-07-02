from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TaskStatus:
    PENDING = "pending"
    COMPLETED = "completed"


class TaskTrackerCreate(BaseModel):
    task_id: str | None = None
    task_name: str
    assigned_to: str | None = None
    meeting_id: str | None = None
    deadline: str | None = None
    status: str = TaskStatus.PENDING


class TaskTrackerUpdateStatus(BaseModel):
    status: str = Field(description="pending or completed")


class TaskTrackerInDB(BaseModel):
    id: str = Field(alias="_id")
    task_id: str
    task_name: str
    assigned_to: str | None = None
    meeting_id: str | None = None
    deadline: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class TaskTrackerOut(BaseModel):
    id: str
    task_id: str
    task_name: str
    assigned_to: str | None = None
    meeting_id: str | None = None
    deadline: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

