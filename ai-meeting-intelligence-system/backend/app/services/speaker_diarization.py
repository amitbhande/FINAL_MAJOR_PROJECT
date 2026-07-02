from __future__ import annotations

import gc
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def _map_speakers_to_names(segments: list[dict[str, Any]], participants: list[str]) -> dict[str, str]:
    order: list[str] = []
    for seg in segments:
        sid = seg.get("speaker")
        if isinstance(sid, str) and sid and sid not in order:
            order.append(sid)
    out: dict[str, str] = {}
    for i, sid in enumerate(order):
        out[sid] = participants[i].strip() if i < len(participants) and participants[i].strip() else f"Speaker {i + 1}"
    return out


def _build_outputs(
    segments: list[dict[str, Any]], name_map: dict[str, str]
) -> tuple[str, str, list[dict[str, Any]]]:
    plain_parts: list[str] = []
    labeled_lines: list[str] = []
    structured: list[dict[str, Any]] = []

    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        sp = seg.get("speaker")
        sp_id = sp if isinstance(sp, str) else "UNKNOWN"
        display = name_map.get(sp_id, sp_id)
        plain_parts.append(text)
        labeled_lines.append(f"{display}: {text}")
        structured.append(
            {
                "speaker": display,
                "speaker_id": sp_id,
                "text": text,
                "start": seg.get("start"),
                "end": seg.get("end"),
            }
        )

    plain = " ".join(plain_parts)
    labeled = "\n".join(labeled_lines)
    return plain, labeled, structured


def transcribe_with_speakers(audio_path: Path, participants: list[str]) -> tuple[str, str, list[dict[str, Any]]] | None:
    """
    WhisperX ASR + alignment + pyannote diarization. Requires optional deps (see requirements-diarization.txt)
    and a Hugging Face token with access to pyannote/speaker-diarization-community-1.
    Returns (plain_text, labeled_transcript, speaker_segments) or None on failure / missing deps.
    """
    if not settings.enable_speaker_diarization:
        return None
    token = settings.huggingface_token
    if not (token or "").strip():
        logger.warning("Speaker diarization enabled but HUGGINGFACE_TOKEN is not set")
        return None

    try:
        import whisperx
        from whisperx.diarize import DiarizationPipeline
    except ImportError:
        logger.warning("whisperx not installed; install with: pip install -r requirements-diarization.txt")
        return None

    device = settings.whisperx_device
    compute_type = settings.whisperx_compute_type
    batch_size = settings.whisperx_batch_size
    model_name = settings.whisperx_model or settings.whisper_model

    try:
        audio = whisperx.load_audio(str(audio_path))
        model = whisperx.load_model(model_name, device, compute_type=compute_type)
        result = model.transcribe(audio, batch_size=batch_size)
        del model
        gc.collect()

        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
        del model_a
        gc.collect()

        try:
            diarize_model = DiarizationPipeline(token=token.strip(), device=device)
        except TypeError:
            diarize_model = DiarizationPipeline(use_auth_token=token.strip(), device=device)
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        del diarize_model
        gc.collect()
    except Exception:
        logger.exception("WhisperX diarization pipeline failed")
        return None

    raw_segments = result.get("segments") or []
    if not raw_segments:
        return None

    name_map = _map_speakers_to_names(raw_segments, participants)
    plain, labeled, structured = _build_outputs(raw_segments, name_map)
    if not plain.strip():
        return None
    return plain.strip(), labeled, structured
