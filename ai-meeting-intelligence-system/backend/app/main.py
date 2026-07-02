from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.graph import router as graph_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.api.meetings import router as meetings_router
from app.api.task_tracker import router as task_tracker_router
from app.api.transcribe import router as transcribe_router
from app.api.transcripts import router as transcripts_router
from app.api.uploads import router as uploads_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.chroma import connect_chroma, disconnect_chroma
from app.db.mongo import connect_mongo, disconnect_mongo
from app.services.llm import llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await connect_mongo()
    connect_chroma()
    yield
    disconnect_chroma()
    await disconnect_mongo()
    await llm.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS: explicit list from settings + in dev, regex so localhost / 127.0.0.1 on any port match
# (browsers treat localhost vs 127.0.0.1 as different origins; wrong .env can omit one).
_cors: dict = {
    "allow_origins": settings.cors_origins_list(),
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.env == "dev":
    _cors["allow_origin_regex"] = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

app.add_middleware(CORSMiddleware, **_cors)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(meetings_router)
app.include_router(rag_router)
app.include_router(task_tracker_router)
app.include_router(uploads_router)
app.include_router(transcribe_router)
app.include_router(transcripts_router)
app.include_router(graph_router)

