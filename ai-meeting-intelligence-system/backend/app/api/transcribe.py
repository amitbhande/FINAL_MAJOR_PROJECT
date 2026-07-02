from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.services.audio_prep import AudioPrepError, normalize_for_transcription
from app.services.transcription import transcriber

router = APIRouter(prefix="/transcribe", tags=["transcription"])


class TranscribeResponse(BaseModel):
    transcript: str
    language: str | None = None
    duration: float | None = None
    original_path: str
    prepared_path: str


@router.post("", response_model=TranscribeResponse)
async def transcribe_meeting_audio(audio: UploadFile = File(...)) -> TranscribeResponse:
    """
    Steps:
    1) Load audio upload (mp3/wav)
    2) Normalize it for transcription (16kHz mono wav)
    3) Transcribe using Whisper
    4) Return transcript JSON
    """
    ext = _validate_extension(audio)

    uploads_dir = Path(settings.uploads_dir).resolve()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid4().hex
    original_path = uploads_dir / f"{file_id}{ext}"
    prepared_path = uploads_dir / f"{file_id}.prepared.wav"

    try:
        await _stream_to_disk(audio, original_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}") from e

    try:
        normalize_for_transcription(original_path, prepared_path)
    except AudioPrepError as e:
        raise HTTPException(status_code=503, detail=f"Audio prep failed: {e}") from e

    try:
        result = transcriber.transcribe_file(prepared_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}") from e

    transcript = (result.get("text") or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Empty transcript returned by Whisper")

    return TranscribeResponse(
        transcript=transcript,
        language=result.get("language"),
        duration=result.get("duration"),
        original_path=str(original_path),
        prepared_path=str(prepared_path),
    )


def _validate_extension(audio: UploadFile) -> str:
    filename = (audio.filename or "").lower()
    for ext in (".mp3", ".wav", ".mp4", ".m4a", ".aac", ".ogg", ".webm", ".mov", ".mkv"):
        if filename.endswith(ext):
            return ext

    ct = (audio.content_type or "").lower()
    if ct in {"audio/mpeg", "audio/mp3"}:
        return ".mp3"
    if ct in {"audio/wav", "audio/x-wav", "audio/wave"}:
        return ".wav"
    if ct in {"video/mp4", "audio/mp4"}:
        return ".mp4"
    raise HTTPException(
        status_code=415,
        detail="Supported: .mp3, .wav, .mp4, .m4a, .aac, .ogg, .webm, .mov, .mkv",
    )


async def _stream_to_disk(upload: UploadFile, path: Path, chunk_size: int = 1024 * 1024) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        while True:
            chunk = await upload.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)

