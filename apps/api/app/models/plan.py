"""Preparation plan, rounds, and tasks."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RoundType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PreparationPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "preparation_plans"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    project = relationship("InterviewProject", back_populates="plan")
    rounds = relationship(
        "PreparationRound",
        back_populates="plan",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PreparationRound.priority",
    )
    tasks = relationship(
        "PreparationTask",
        back_populates="plan",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PreparationTask.priority",
    )


class PreparationRound(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "preparation_rounds"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("preparation_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    round_type: Mapped[str] = mapped_column(String(64), nullable=False, default=RoundType.TECHNICAL)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text)

    plan = relationship("PreparationPlan", back_populates="rounds")
    sessions = relationship("PracticeSession", back_populates="round", lazy="selectin")


class PreparationTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "preparation_tasks"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("preparation_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    round_type: Mapped[str] = mapped_column(String(64), nullable=False, default=RoundType.TECHNICAL)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    due_date_offset_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_today: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    plan = relationship("PreparationPlan", back_populates="tasks")
