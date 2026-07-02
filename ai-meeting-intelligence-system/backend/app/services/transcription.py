from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import whisper  # type: ignore
except Exception:  # pragma: no cover
    whisper = None

from app.core.config import settings
from app.services.audio_prep import AudioPrepError, normalize_for_transcription

# Video / container formats: decode with ffmpeg to 16 kHz mono WAV first so the
# audio track is reliably extracted (matches /transcribe + uploads flow).
_FFMPEG_FIRST_SUFFIXES = frozenset({".mp4", ".mov", ".mkv", ".webm"})


@dataclass
class MeetingTranscriptionResult:
    """Plain transcript for search/storage; optional diarization from WhisperX."""

    transcript_text: str
    speaker_segments: list[dict[str, Any]] | None = None
    labeled_transcript: str | None = None


def _prepare_work_audio_path(td_path: Path, audio_bytes: bytes, suffix: str) -> Path:
    suf = (suffix or ".mp3").lower().strip()
    if not suf.startswith("."):
        suf = "." + suf

    if suf in _FFMPEG_FIRST_SUFFIXES:
        original = td_path / f"input{suf}"
        prepared = td_path / "prepared.wav"
        original.write_bytes(audio_bytes)
        try:
            normalize_for_transcription(original, prepared)
            return prepared
        except AudioPrepError:
            return original

    p = td_path / f"audio{suf}"
    p.write_bytes(audio_bytes)
    return p


def _prepare_work_audio_path_from_path(td_path: Path, source_path: Path) -> Path:
    suf = source_path.suffix.lower() or ".mp3"
    if suf in _FFMPEG_FIRST_SUFFIXES:
        original = td_path / f"input{suf}"
        prepared = td_path / "prepared.wav"
        shutil.copy2(source_path, original)
        try:
            normalize_for_transcription(original, prepared)
            return prepared
        except AudioPrepError:
            return original

    p = td_path / f"audio{suf}"
    shutil.copy2(source_path, p)
    return p


class WhisperTranscriber:
    def __init__(self) -> None:
        self._model = None

    def transcribe_file(self, audio_path: Path) -> dict:
        if whisper is None:
            raise RuntimeError(
                "Transcription dependency not installed. Install with: pip install openai-whisper"
            )
        if self._model is None:
            self._model = whisper.load_model(settings.whisper_model)
        return self._model.transcribe(str(audio_path))

    def transcribe_meeting_upload(
        self, audio_bytes: bytes, suffix: str, participants: list[str]
    ) -> MeetingTranscriptionResult:
        """
        Transcribe upload; optionally run WhisperX diarization when enabled + HF token set.
        """
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            work_path = _prepare_work_audio_path(td_path, audio_bytes, suffix)

            from app.services.speaker_diarization import transcribe_with_speakers

            # 1) Optional diarization (best-effort). If it fails/returns None,
            #    or the upload is large, we fall back to plain Whisper.
            try:
                diarization_allowed = (
                    settings.enable_speaker_diarization
                    and len(audio_bytes) <= settings.speaker_diarization_max_bytes
                )
                wx = transcribe_with_speakers(work_path, participants) if diarization_allowed else None
                if wx is not None:
                    plain, labeled, segments = wx
                    return MeetingTranscriptionResult(
                        transcript_text=plain,
                        speaker_segments=segments,
                        labeled_transcript=labeled,
                    )
            except Exception as e:
                # Do not fail the whole upload due to diarization.
                # Whisper-only fallback will run below.
                pass

            # 2) Plain Whisper (required)
            try:
                result = self.transcribe_file(work_path)
            except Exception as e:
                raise RuntimeError(f"Whisper transcription failed: {type(e).__name__}: {e}") from e

            text = (result.get("text") or "").strip()
            return MeetingTranscriptionResult(transcript_text=text)

    def transcribe_meeting_upload_path(self, audio_path: Path, participants: list[str]) -> MeetingTranscriptionResult:
        """Transcribe an already-saved upload file path with optional diarization."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            work_path = _prepare_work_audio_path_from_path(td_path, audio_path)

            from app.services.speaker_diarization import transcribe_with_speakers

            try:
                diarization_allowed = (
                    settings.enable_speaker_diarization
                    and audio_path.stat().st_size <= settings.speaker_diarization_max_bytes
                )
                wx = transcribe_with_speakers(work_path, participants) if diarization_allowed else None
                if wx is not None:
                    plain, labeled, segments = wx
                    return MeetingTranscriptionResult(
                        transcript_text=plain,
                        speaker_segments=segments,
                        labeled_transcript=labeled,
                    )
            except Exception:
                pass

            try:
                result = self.transcribe_file(work_path)
            except Exception as e:
                raise RuntimeError(f"Whisper transcription failed: {type(e).__name__}: {e}") from e

            text = (result.get("text") or "").strip()
            return MeetingTranscriptionResult(transcript_text=text)

    def transcribe_bytes(self, audio_bytes: bytes, suffix: str = ".mp3") -> str:
        """Plain OpenAI Whisper only (no diarization). Used by /transcribe and other callers."""
        if whisper is None:
            raise RuntimeError(
                "Transcription dependency not installed. Install with: pip install openai-whisper"
            )
        if self._model is None:
            self._model = whisper.load_model(settings.whisper_model)

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            work_path = _prepare_work_audio_path(td_path, audio_bytes, suffix)
            result = self.transcribe_file(work_path)
            return (result.get("text") or "").strip()


transcriber = WhisperTranscriber()
