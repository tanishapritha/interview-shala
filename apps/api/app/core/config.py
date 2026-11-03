"""Application settings loaded from environment / .env."""

from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Interview Shala API"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/interview_shala",
        description="Async SQLAlchemy database URL",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_asyncpg_ssl_parameter(cls, value: object) -> object:
        """Translate libpq's sslmode parameter to asyncpg's ssl parameter.

        Hosted PostgreSQL providers commonly supply URLs ending in
        ?sslmode=require. SQLAlchemy's asyncpg dialect forwards query
        parameters to asyncpg, which expects ssl instead of sslmode.
        """
        if not isinstance(value, str) or not value.startswith("postgresql+asyncpg://"):
            return value

        parsed = urlsplit(value)
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        if not any(key == "sslmode" for key, _ in query_items):
            return value

        has_ssl = any(key == "ssl" for key, _ in query_items)
        normalized_items = [
            (key, item)
            for key, item in query_items
            if key != "sslmode"
        ]
        if not has_ssl:
            sslmode_value = next(
                item for key, item in query_items if key == "sslmode"
            )
            normalized_items.append(("ssl", sslmode_value))

        return urlunsplit(parsed._replace(query=urlencode(normalized_items)))

    clerk_secret_key: str | None = None
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None
    clerk_audience: str | None = None

    livekit_api_key: str | None = None
    livekit_api_secret: str | None = None
    livekit_url: str | None = None

    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    llm_model: str = "llama-3.3-70b-versatile"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"

    encryption_key: str | None = None
    anonymous_session_secret: str = "change-me-in-production"
    anonymous_session_ttl_days: int = 30

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items
        return value

    @property
    def livekit_configured(self) -> bool:
        return bool(self.livekit_api_key and self.livekit_api_secret and self.livekit_url)

    @property
    def clerk_configured(self) -> bool:
        return bool(self.clerk_jwks_url)

    @property
    def llm_configured(self) -> bool:
        return bool(self.groq_api_key or self.openrouter_api_key)

    @property
    def sync_database_url(self) -> str:
        """Alembic-friendly sync URL derived from the async URL."""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
