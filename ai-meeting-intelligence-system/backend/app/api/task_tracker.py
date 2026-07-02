from __future__ import annotations

from fastapi import APIRouter
from app.models.task_tracker import TaskTrackerCreate, TaskTrackerOut, TaskTrackerUpdateStatus
from app.repositories.task_tracker import create_task, delete_task, list_tasks, update_task_status

router = APIRouter(prefix="/tasks", tags=["task-tracker"])


@router.post("", response_model=TaskTrackerOut)
async def create(payload: TaskTrackerCreate) -> TaskTrackerOut:
    return await create_task(payload)


@router.patch("/{task_id}/status", response_model=TaskTrackerOut)
async def update_status(task_id: str, payload: TaskTrackerUpdateStatus) -> TaskTrackerOut:
    return await update_task_status(task_id, payload.status)


@router.get("", response_model=list[TaskTrackerOut])
async def list_all(
    meeting_id: str | None = None,
    assigned_to: str | None = None,
    status: str | None = None,
    limit: int = 10000,
) -> list[TaskTrackerOut]:
    return await list_tasks(meeting_id=meeting_id, assigned_to=assigned_to, status=status, limit=limit)


@router.delete("/{task_id}")
async def delete(task_id: str) -> dict:
    return await delete_task(task_id)

