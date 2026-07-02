from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.db.mongo import mongo
from app.services.vector_store import query as chroma_query


async def search_meetings(query: str, top_k: int = 8) -> list[dict[str, Any]]:
    """
    Semantic search across meetings using ChromaDB.

    Returns a list of relevant meetings with:
    - meeting_id
    - title
    - transcript_text
    - top_chunks (most relevant retrieved chunks)
    """
    q = (query or "").strip()
    if not q:
        return []
    if mongo.db is None:
        raise RuntimeError("Mongo not initialized")

    hits = chroma_query(q, top_k=top_k)
    if not hits:
        return []

    by_meeting: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for h in hits:
        mid = h.get("meeting_id")
        if mid:
            by_meeting[str(mid)].append(h)

    meeting_ids = list(by_meeting.keys())

    # Fetch from meeting_transcripts (keyed by meeting_id string)
    transcripts = await mongo.db.meeting_transcripts.find({"meeting_id": {"$in": meeting_ids}}).to_list(length=len(meeting_ids))
    transcripts_by_id = {t.get("meeting_id"): t for t in transcripts if t.get("meeting_id")}

    results: list[dict[str, Any]] = []
    for mid in meeting_ids:
        chunks = sorted(by_meeting[mid], key=lambda x: float(x.get("distance") or 0.0))[:3]
        tdoc = transcripts_by_id.get(mid)
        if tdoc:
            results.append(
                {
                    "meeting_id": mid,
                    "title": tdoc.get("meeting_title"),
                    "transcript_text": tdoc.get("transcript", ""),
                    "summary": tdoc.get("summary"),
                    "top_chunks": chunks,
                }
            )
            continue

        # Fall back to meetings collection if present.
        try:
            from bson import ObjectId

            mdoc = await mongo.db.meetings.find_one({"_id": ObjectId(mid)})
        except Exception:
            mdoc = None

        if mdoc:
            results.append(
                {
                    "meeting_id": mid,
                    "title": mdoc.get("title"),
                    "transcript_text": mdoc.get("transcript_text", ""),
                    "summary": mdoc.get("summary"),
                    "top_chunks": chunks,
                }
            )

    return results

