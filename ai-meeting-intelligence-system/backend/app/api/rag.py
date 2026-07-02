from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.db.chroma import chroma
from app.services.rag_pipeline import ask_about_meetings

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/chroma-view")
async def chroma_view() -> dict[str, Any]:
    """
    View all data stored in ChromaDB (documents, ids, metadatas).
    Use for debugging or inspecting stored transcript chunks.
    """
    if chroma.collection is None:
        return {"ok": False, "message": "ChromaDB not initialized", "items": []}
    res = chroma.collection.get(include=["documents", "metadatas"])
    ids = res.get("ids") or []
    docs = res.get("documents") or []
    metas = res.get("metadatas") or []
    items = [
        {"id": _id, "document": doc, "metadata": meta}
        for _id, doc, meta in zip(ids, docs, metas)
    ]
    return {"ok": True, "count": len(items), "items": items}


class RagAskRequest(BaseModel):
    question: str
    top_k: int = 8


class ReferencedMeeting(BaseModel):
    meeting_id: str
    title: str | None = None


class RagAskResponse(BaseModel):
    question: str
    answer: str
    referenced_meetings: list[ReferencedMeeting] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/ask", response_model=RagAskResponse)
async def rag_ask(payload: RagAskRequest) -> RagAskResponse:
    out = await ask_about_meetings(payload.question, top_k=payload.top_k)
    return RagAskResponse(**out)

