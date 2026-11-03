"""Auth-related schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import APIModel


class AnonymousSessionResponse(APIModel):
    session_id: str
    expires_in_days: int


class MigrateAnonymousRequest(APIModel):
    anonymous_session_id: str | None = None


class CurrentUserResponse(APIModel):
    id: UUID
    email: str | None = None
    display_name: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None
