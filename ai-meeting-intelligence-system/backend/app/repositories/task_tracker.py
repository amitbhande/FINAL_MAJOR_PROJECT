from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.db.mongo import mongo
from app.models.task_tracker import TaskStatus, TaskTrackerCreate, TaskTrackerOut
from app.utils.ids import oid_str

from pymongo import ReturnDocument

COLL = "task_tracker"


def _validate_status(status: str) -> str:
    s = (status or "").strip().lower()
    if s not in {TaskStatus.PENDING, TaskStatus.COMPLETED}:
        raise HTTPException(status_code=400, detail="status must be 'pending' or 'completed'")
    return s


async def create_task(payload: TaskTrackerCreate) -> TaskTrackerOut:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    now = datetime.now(timezone.utc)
    task_id = (payload.task_id or "").strip() or uuid4().hex
    status = _validate_status(payload.status)

    doc = {
        "task_id": task_id,
        "task_name": payload.task_name.strip(),
        "assigned_to": (payload.assigned_to or None),
        "meeting_id": (payload.meeting_id or None),
        "deadline": (payload.deadline or None),
        "status": status,
        "created_at": now,
        "updated_at": now,
    }

    try:
        ins = await mongo.db[COLL].insert_one(doc)
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"task_id already exists: {task_id}") from e

    return TaskTrackerOut(id=oid_str(ins.inserted_id), **doc)


async def update_task_status(task_id: str, status: str) -> TaskTrackerOut:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    s = _validate_status(status)
    now = datetime.now(timezone.utc)

    doc = await mongo.db[COLL].find_one_and_update(
        {"task_id": task_id},
        {"$set": {"status": s, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskTrackerOut(
        id=oid_str(doc["_id"]),
        task_id=doc["task_id"],
        task_name=doc["task_name"],
        assigned_to=doc.get("assigned_to"),
        meeting_id=doc.get("meeting_id"),
        deadline=doc.get("deadline"),
        status=doc.get("status"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


async def list_tasks(
    *,
    meeting_id: str | None = None,
    assigned_to: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[TaskTrackerOut]:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    q: dict = {}
    if meeting_id:
        q["meeting_id"] = meeting_id
    if assigned_to:
        q["assigned_to"] = assigned_to
    if status:
        q["status"] = _validate_status(status)

    cur = mongo.db[COLL].find(q).sort("updated_at", -1).limit(min(limit, 10000))
    out: list[TaskTrackerOut] = []
    async for doc in cur:
        out.append(
            TaskTrackerOut(
                id=oid_str(doc["_id"]),
                task_id=doc["task_id"],
                task_name=doc["task_name"],
                assigned_to=doc.get("assigned_to"),
                meeting_id=doc.get("meeting_id"),
                deadline=doc.get("deadline"),
                status=doc.get("status"),
                created_at=doc.get("created_at"),
                updated_at=doc.get("updated_at"),
            )
        )
    return out


async def delete_task(task_id: str) -> dict:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    res = await mongo.db[COLL].delete_one({"task_id": task_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True, "task_id": task_id}

