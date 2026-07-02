from __future__ import annotations

from pydantic import AliasChoices, AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Meeting Intelligence System"
    env: str = "dev"

    # Include both hostnames — browsers treat localhost and 127.0.0.1 as different origins.
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "aimis"

    chroma_persist_dir: str = "./storage/chroma"
    chroma_collection: str = "meeting_transcripts"

    uploads_dir: str = "./storage/uploads"

    # LLM providers
    # - OpenAI-compatible: set LLM_API_KEY (+ optional base/model)
    # - Gemini: set GEMINI_API_KEY (+ optional model)
    llm_api_key: str | None = None
    llm_base_url: AnyHttpUrl = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    whisper_model: str = "base"

    # Optional: speaker diarization via WhisperX + pyannote (see requirements-diarization.txt)
    enable_speaker_diarization: bool = False
    huggingface_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("HUGGINGFACE_TOKEN", "HF_TOKEN"),
    )
    whisperx_device: str = "cpu"
    whisperx_compute_type: str = "int8"
    whisperx_batch_size: int = 8
    whisperx_model: str | None = None

    # WhisperX diarization is expensive and can fail/OOM on large uploads.
    # When above this size, diarization is skipped and we fall back to plain Whisper.
    speaker_diarization_max_bytes: int = 25 * 1024 * 1024

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()

