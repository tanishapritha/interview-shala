"""Weakness schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import Severity
from app.schemas.common import APIModel


class WeaknessResponse(APIModel):
    id: UUID
    skill: str
    severity: Severity
    observation_count: int
    summary: str
    evidence: list[str] = Field(default_factory=list)
    recommended_exercise: str
    recent_progress: float | None = None
    updated_at: datetime
