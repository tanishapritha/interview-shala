"""Practice sessions, skill assessments, and session events."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RoundType, SessionStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PracticeSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "practice_sessions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("preparation_rounds.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    round_type: Mapped[str] = mapped_column(String(64), nullable=False, default=RoundType.TECHNICAL)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=SessionStatus.PENDING)
    score: Mapped[float | None] = mapped_column(Float)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    questions_completed: Mapped[int | None] = mapped_column(Integer)
    strengths: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    improvements: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    next_action: Mapped[str | None] = mapped_column(Text)
    livekit_room_name: Mapped[str | None] = mapped_column(String(255))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project = relationship("InterviewProject", back_populates="sessions")
    round = relationship("PreparationRound", back_populates="sessions")
    questions = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    skill_assessments = relationship(
        "SkillAssessment",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events = relationship(
        "SessionEvent",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SkillAssessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "skill_assessments"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    notes: Mapped[str | None] = mapped_column(Text)

    session = relationship("PracticeSession", back_populates="skill_assessments")


class SessionEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "session_events"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    session = relationship("PracticeSession", back_populates="events")
