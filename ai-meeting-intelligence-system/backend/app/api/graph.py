from __future__ import annotations

from fastapi import APIRouter
from app.db.mongo import mongo
from app.utils.ids import oid_str

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def graph() -> dict:
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    meetings = []
    async for m in mongo.db.meetings.find({}, {"title": 1, "participants": 1, "created_at": 1, "action_items": 1}).sort("created_at", -1).limit(10000):
        meetings.append(m)

    nodes: list[dict] = []
    edges: list[dict] = []

    def add_node(node_id: str, label: str, kind: str, **attrs) -> None:
        nodes.append({"id": node_id, "label": label, "kind": kind, **attrs})

    def add_edge(src: str, dst: str, kind: str) -> None:
        edges.append({"source": src, "target": dst, "kind": kind})

    participants_seen: set[str] = set()

    for m in meetings:
        mid = oid_str(m["_id"])
        add_node(mid, m.get("title") or "Meeting", "meeting", created_at=str(m.get("created_at")))

        for p in m.get("participants") or []:
            pid = f"person:{p}"
            if pid not in participants_seen:
                add_node(pid, p, "person")
                participants_seen.add(pid)
            add_edge(pid, mid, "attended")

        for i, ai in enumerate(m.get("action_items") or []):
            tid = f"task:{mid}:{i}"
            add_node(tid, ai.get("title") or "Task", "task", status=ai.get("status", "open"), owner=ai.get("owner"))
            add_edge(mid, tid, "has_task")
            if ai.get("owner"):
                pid = f"person:{ai['owner']}"
                if pid not in participants_seen:
                    add_node(pid, ai["owner"], "person")
                    participants_seen.add(pid)
                add_edge(pid, tid, "owns")

    return {"nodes": nodes, "edges": edges}

