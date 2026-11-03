"""Persistent candidate knowledge, transcript, and evidence models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeConcept(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical, reusable concept in the interview knowledge taxonomy."""

    __tablename__ = "knowledge_concepts"
    __table_args__ = (
        UniqueConstraint("key", name="uq_knowledge_concepts_key"),
        CheckConstraint("key = lower(key)", name="ck_knowledge_concepts_key_lowercase"),
        Index("ix_knowledge_concepts_parent_id", "parent_id"),
    )

    key: Mapped[str] = mapped_column(String(160), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_concepts.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class ProjectKnowledgeConcept(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A concept required or recommended for one interview project."""

    __tablename__ = "project_knowledge_concepts"
    __table_args__ = (
        UniqueConstraint("project_id", "concept_id", name="uq_project_knowledge_concept"),
        CheckConstraint("importance >= 1 AND importance <= 5", name="ck_project_concept_importance"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    target_depth: Mapped[str] = mapped_column(String(32), nullable=False, default="working")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="inferred")
    source_reference: Mapped[str | None] = mapped_column(Text)


class CandidateSkillProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Cross-session skill state; values remain unknown until evidence supports them."""

    __tablename__ = "candidate_skill_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_key", name="uq_candidate_skill_profile"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_candidate_skill_confidence",
        ),
        CheckConstraint(
            "proficiency IS NULL OR (proficiency >= 0 AND proficiency <= 5)",
            name="ck_candidate_skill_proficiency",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_key: Mapped[str] = mapped_column(String(160), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    proficiency: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assessment_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unassessed"
    )


class SessionTranscriptSegment(UUIDPrimaryKeyMixin, Base):
    """Append-only transcript segment with stable ordering within a session."""

    __tablename__ = "session_transcript_segments"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_number", name="uq_transcript_session_sequence"),
        CheckConstraint("sequence_number >= 0", name="ck_transcript_sequence_nonnegative"),
        CheckConstraint("elapsed_ms IS NULL OR elapsed_ms >= 0", name="ck_transcript_elapsed_nonnegative"),
        CheckConstraint(
            "speaker IN ('candidate', 'interviewer', 'system')",
            name="ck_transcript_speaker",
        ),
        Index("ix_transcript_session_created", "session_id", "created_at"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)
    is_final: Mapped[bool] = mapped_column(nullable=False, default=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="livekit")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CandidateEvidence(UUIDPrimaryKeyMixin, Base):
    """Auditable observation tied to the candidate and its source material."""

    __tablename__ = "candidate_evidence"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_candidate_evidence_confidence",
        ),
        Index("ix_candidate_evidence_user_observed", "user_id", "observed_at"),
        Index("ix_candidate_evidence_project_concept", "project_id", "concept_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    concept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_concepts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transcript_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session_transcript_segments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    polarity: Mapped[str] = mapped_column(String(16), nullable=False, default="neutral")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
