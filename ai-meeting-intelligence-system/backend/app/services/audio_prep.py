from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class AudioPrepError(RuntimeError):
    pass


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def normalize_for_transcription(input_path: Path, output_path: Path) -> Path:
    """
    Normalize audio into a Whisper-friendly WAV:
    - mono
    - 16kHz sample rate
    - 16-bit PCM
    """
    ensure_dir(output_path.parent)

    if shutil.which("ffmpeg") is None:
        raise AudioPrepError(
            "ffmpeg binary not found in PATH. "
            "Install ffmpeg and ensure it is available in your system PATH. "
            "On Windows use Chocolatey/scoop or download from https://ffmpeg.org/. "
            "Then restart your terminal and retry."
        )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        # Video containers often confuse the default stream selection; force audio-only.
        "-vn",
        "-map",
        "0:a:0",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise AudioPrepError("ffmpeg not found on PATH") from e

    if p.returncode != 0:
        raise AudioPrepError((p.stderr or p.stdout or "ffmpeg failed").strip())
    return output_path

