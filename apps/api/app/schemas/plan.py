"""Preparation plan schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.enums import RoundType
from app.schemas.common import APIModel


class PreparationTaskResponse(APIModel):
    id: UUID
    title: str
    description: str | None = None
    round_type: RoundType
    priority: int = 1
    completed: bool = False
    estimated_minutes: int | None = None


class PreparationTaskUpdate(APIModel):
    completed: bool | None = None
    title: str | None = None
    description: str | None = None
    priority: int | None = None


class PreparationRoundResponse(APIModel):
    id: UUID
    name: str
    round_type: RoundType
    priority: int = 1
    progress_percent: int = 0
    topics: list[str] = Field(default_factory=list)
    question_count: int = 0
    description: str | None = None


class PreparationPlanResponse(APIModel):
    id: UUID
    project_id: UUID
    summary: str
    rounds: list[PreparationRoundResponse] = Field(default_factory=list)
    tasks: list[PreparationTaskResponse] = Field(default_factory=list)
    today_tasks: list[PreparationTaskResponse] = Field(default_factory=list)
