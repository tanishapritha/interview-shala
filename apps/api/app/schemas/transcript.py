"""Transcript ingestion and retrieval schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import APIModel


class TranscriptSegmentCreate(APIModel):
    sequence_number: int = Field(ge=0)
    speaker: Literal["candidate", "interviewer"]
    text: str = Field(min_length=1, max_length=20_000)
    elapsed_ms: int | None = Field(default=None, ge=0)
    is_final: bool = True


class TranscriptSegmentResponse(APIModel):
    id: UUID
    session_id: UUID
    sequence_number: int
    speaker: str
    text: str
    elapsed_ms: int | None
    is_final: bool
    source: str
    created_at: datetime


class TranscriptIngestResponse(APIModel):
    accepted: int
    already_present: int
    segments: list[TranscriptSegmentResponse]
    trust_level: Literal["client_supplied"] = "client_supplied"
