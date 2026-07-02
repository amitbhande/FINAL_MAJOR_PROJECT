from __future__ import annotations

from typing import Any

from app.services.llm import rag_answer
from app.services.meeting_memory import search_meetings


async def ask_about_meetings(question: str, top_k: int = 8) -> dict[str, Any]:
    """
    RAG pipeline:
    1) Embed query (handled by Chroma query function)
    2) Retrieve relevant transcript chunks from ChromaDB
    3) Send context to LLM
    4) Return final answer + referenced meetings
    """
    meetings = await search_meetings(question, top_k=top_k)

    # Flatten chunks across meetings for LLM context.
    chunks: list[dict[str, Any]] = []
    for m in meetings:
        for c in (m.get("top_chunks") or []):
            chunks.append(c)

    answer = await rag_answer(question, chunks)
    referenced_meetings = [{"meeting_id": m.get("meeting_id"), "title": m.get("title")} for m in meetings]

    return {
        "question": question,
        "answer": answer,
        "referenced_meetings": referenced_meetings,
        "sources": chunks,
    }

