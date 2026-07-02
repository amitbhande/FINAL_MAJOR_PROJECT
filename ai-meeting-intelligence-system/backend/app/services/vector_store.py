from __future__ import annotations

from dataclasses import dataclass

from app.db.chroma import chroma
from app.services.embeddings import cheap_hash_embedding


@dataclass(frozen=True)
class Chunk:
    meeting_id: str
    chunk_id: str
    text: str


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> list[str]:
    t = text.strip()
    if not t:
        return []
    out: list[str] = []
    i = 0
    while i < len(t):
        out.append(t[i : i + max_chars])
        i += max_chars - overlap
        if i < 0:
            i = max_chars
    return out


def upsert_transcript(meeting_id: str, transcript: str) -> int:
    if chroma.collection is None:
        return 0

    chunks = chunk_text(transcript)
    ids = [f"{meeting_id}:{i}" for i in range(len(chunks))]
    embeddings = [cheap_hash_embedding(c) for c in chunks]
    metadatas = [{"meeting_id": meeting_id, "chunk_index": i} for i in range(len(chunks))]
    chroma.collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return len(chunks)


def _plain_int(v) -> int | None:
    if v is None:
        return None
    return int(v)


def _plain_float(v) -> float | None:
    if v is None:
        return None
    return float(v)


def query(question: str, top_k: int = 6) -> list[dict]:
    if chroma.collection is None:
        return []
    q_emb = cheap_hash_embedding(question)
    try:
        # NOTE: Some Chroma versions reject "ids" inside include; ids are returned separately as res["ids"].
        res = chroma.collection.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    ids = (res.get("ids") or [[]])[0]
    out: list[dict] = []
    for doc, meta, dist, _id in zip(docs, metas, dists, ids):
        mid = (meta or {}).get("meeting_id")
        out.append(
            {
                "chunk": doc if isinstance(doc, str) else str(doc),
                "meeting_id": str(mid) if mid is not None else None,
                "chunk_index": _plain_int((meta or {}).get("chunk_index")),
                "distance": _plain_float(dist),
                "id": str(_id) if _id is not None else None,
            }
        )
    return out

