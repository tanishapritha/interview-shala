"""Interview questions and answers."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RoundType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InterviewQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_questions"

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    round_type: Mapped[str] = mapped_column(String(64), nullable=False, default=RoundType.TECHNICAL)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_topics: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str | None] = mapped_column(String(64))

    session = relationship("PracticeSession", back_populates="questions")
    answers = relationship(
        "InterviewAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class InterviewAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_answers"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    transcript: Mapped[str | None] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(String(2048))
    score: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    question = relationship("InterviewQuestion", back_populates="answers")
