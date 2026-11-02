"""Auth-related schemas."""

from __future__ import annotations

from app.schemas.common import APIModel


class AnonymousSessionResponse(APIModel):
    session_id: str
    expires_in_days: int


class MigrateAnonymousRequest(APIModel):
    anonymous_session_id: str | None = None
