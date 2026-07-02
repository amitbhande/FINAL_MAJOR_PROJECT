from __future__ import annotations

try:
    import chromadb  # type: ignore
except Exception:  # pragma: no cover
    chromadb = None

from app.core.config import settings


class Chroma:
    client = None
    collection = None


chroma = Chroma()


def connect_chroma() -> None:
    if chromadb is None:
        chroma.client = None
        chroma.collection = None
        return
    chroma.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    chroma.collection = chroma.client.get_or_create_collection(name=settings.chroma_collection, metadata={"hnsw:space": "cosine"})


def disconnect_chroma() -> None:
    chroma.client = None
    chroma.collection = None

