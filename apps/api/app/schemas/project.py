"""Interview project schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import APIModel
from app.schemas.plan import PreparationPlanResponse


class InterviewProjectBase(APIModel):
    company: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    job_description: str | None = None
    company_url: str | None = None
    interview_date: date | None = None
    additional_context: str | None = None


class InterviewProjectCreate(InterviewProjectBase):
    pass


class InterviewProjectUpdate(APIModel):
    company: str | None = Field(default=None, min_length=1, max_length=255)
    role: str | None = Field(default=None, min_length=1, max_length=255)
    job_description: str | None = None
    company_url: str | None = None
    interview_date: date | None = None
    additional_context: str | None = None


class InterviewProjectResponse(InterviewProjectBase):
    id: UUID
    readiness_score: float = 0.0
    progress_percent: int = 0
    created_at: datetime
    updated_at: datetime


class QuickStartPayload(InterviewProjectBase):
    """Body for POST /projects/quick-start."""


class QuickStartResponse(APIModel):
    project: InterviewProjectResponse
    plan: PreparationPlanResponse
