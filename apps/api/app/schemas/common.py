"""Shared schema helpers and utility responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class APIModel(BaseModel):
    """Base model with camelCase JSON aliases matching frontend types."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
        ser_json_timedelta="iso8601",
    )


class HealthResponse(APIModel):
    status: str = "ok"
    service: str = "interview-shala-api"
    version: str = "0.1.0"
    timestamp: datetime | None = None


class MessageResponse(APIModel):
    message: str
    details: dict[str, Any] | None = None
