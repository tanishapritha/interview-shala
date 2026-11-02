"""Weakness tracking and evidence."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Severity
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Weakness(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "weaknesses"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(64), nullable=False, default=Severity.MODERATE)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommended_exercise: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recent_progress: Mapped[float | None] = mapped_column(Float)

    project = relationship("InterviewProject", back_populates="weaknesses")
    evidence_items = relationship(
        "WeaknessEvidence",
        back_populates="weakness",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class WeaknessEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "weakness_evidence"

    weakness_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("weaknesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evidence: Mapped[str] = mapped_column(Text, nullable=False)

    weakness = relationship("Weakness", back_populates="evidence_items")
