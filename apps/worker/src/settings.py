"""Environment-backed worker settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    interview_shala_api_url: str = "http://localhost:8000"
    worker_shared_secret: str

    deepgram_api_key: str
    cartesia_api_key: str
    openrouter_api_key: str
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"
    cartesia_voice_id: str = "f786b574-daa5-4673-aa0c-cbe3e8534c02"
    deepgram_model: str = "nova-3"
    stt_language: str = "en-IN"
    request_timeout_seconds: float = Field(default=10.0, gt=0, le=60)


def get_settings() -> WorkerSettings:
    return WorkerSettings()
