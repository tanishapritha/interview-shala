"""Interview project model."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InterviewProject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_projects"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    anonymous_session_id: Mapped[str | None] = mapped_column(String(512), index=True)

    company: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    job_description: Mapped[str | None] = mapped_column(Text)
    company_url: Mapped[str | None] = mapped_column(String(2048))
    interview_date: Mapped[date | None] = mapped_column(Date)
    additional_context: Mapped[str | None] = mapped_column(Text)

    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="projects")
    plan = relationship(
        "PreparationPlan",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sessions = relationship(
        "PracticeSession",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    weaknesses = relationship(
        "Weakness",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
