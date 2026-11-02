"""Practice session schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import RoundType, SessionStatus
from app.schemas.common import APIModel


class SkillScore(APIModel):
    skill: str
    score: float
    max_score: float = 100.0


class PracticeSessionCreate(APIModel):
    project_id: UUID
    round_id: UUID | None = None
    round_type: RoundType = RoundType.TECHNICAL


class PracticeSessionComplete(APIModel):
    duration_seconds: int | None = Field(default=None, ge=0)
    questions_completed: int | None = Field(default=None, ge=0)
    transcript_summary: str | None = None
    skill_scores: list[SkillScore] | None = None
    strengths: list[str] | None = None
    improvements: list[str] | None = None


class PracticeSessionResponse(APIModel):
    id: UUID
    project_id: UUID
    round_id: UUID | None = None
    round_type: RoundType
    status: SessionStatus
    score: float | None = None
    duration_seconds: int | None = None
    questions_completed: int | None = None
    skill_scores: list[SkillScore] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    next_action: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class LiveKitTokenResponse(APIModel):
    token: str
    room_name: str
    livekit_url: str
    session_id: UUID
