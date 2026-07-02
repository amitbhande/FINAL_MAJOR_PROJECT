from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.services.audio_prep import AudioPrepError, normalize_for_transcription

router = APIRouter(prefix="/uploads", tags=["uploads"])


class UploadAudioResponse(BaseModel):
    original_path: str
    prepared_path: str


@router.post("/meeting-audio", response_model=UploadAudioResponse)
async def upload_meeting_audio(audio: UploadFile = File(...)) -> UploadAudioResponse:
    """
    Accept meeting audio (mp3/wav), store locally, and generate a transcription-ready WAV.
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

    return UploadAudioResponse(
        original_path=str(original_path),
        prepared_path=str(prepared_path),
    )


def _validate_extension(audio: UploadFile) -> str:
    filename = (audio.filename or "").lower()
    for ext in (".mp3", ".wav", ".mp4", ".m4a", ".aac", ".ogg", ".webm", ".mov", ".mkv"):
        if filename.endswith(ext):
            return ext

    # Fallback to content-type if filename is missing/weird
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

