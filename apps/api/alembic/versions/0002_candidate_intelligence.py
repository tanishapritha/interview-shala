"""Candidate knowledge, transcript, skill profile, and evidence schema.

Revision ID: 0002_candidate_intelligence
Revises: 0001_initial
Create Date: 2026-11-03
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_candidate_intelligence"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.String(160), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_concepts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("key", name="uq_knowledge_concepts_key"),
        sa.CheckConstraint("key = lower(key)", name="ck_knowledge_concepts_key_lowercase"),
    )
    op.create_index("ix_knowledge_concepts_parent_id", "knowledge_concepts", ["parent_id"])

    op.create_table(
        "project_knowledge_concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("target_depth", sa.String(32), nullable=False, server_default="working"),
        sa.Column("source", sa.String(32), nullable=False, server_default="inferred"),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("project_id", "concept_id", name="uq_project_knowledge_concept"),
        sa.CheckConstraint("importance >= 1 AND importance <= 5", name="ck_project_concept_importance"),
    )
    op.create_index("ix_project_knowledge_concepts_project_id", "project_knowledge_concepts", ["project_id"])
    op.create_index("ix_project_knowledge_concepts_concept_id", "project_knowledge_concepts", ["concept_id"])

    op.create_table(
        "candidate_skill_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_key", sa.String(160), nullable=False),
        sa.Column("skill_name", sa.String(255), nullable=False),
        sa.Column("proficiency", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessment_status", sa.String(32), nullable=False, server_default="unassessed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "skill_key", name="uq_candidate_skill_profile"),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="ck_candidate_skill_confidence"),
        sa.CheckConstraint("proficiency IS NULL OR (proficiency >= 0 AND proficiency <= 5)", name="ck_candidate_skill_proficiency"),
    )
    op.create_index("ix_candidate_skill_profiles_user_id", "candidate_skill_profiles", ["user_id"])

    op.create_table(
        "session_transcript_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.String(32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("source", sa.String(32), nullable=False, server_default="livekit"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("session_id", "sequence_number", name="uq_transcript_session_sequence"),
        sa.CheckConstraint("sequence_number >= 0", name="ck_transcript_sequence_nonnegative"),
        sa.CheckConstraint("elapsed_ms IS NULL OR elapsed_ms >= 0", name="ck_transcript_elapsed_nonnegative"),
        sa.CheckConstraint("speaker IN ('candidate', 'interviewer', 'system')", name="ck_transcript_speaker"),
    )
    op.create_index("ix_session_transcript_segments_session_id", "session_transcript_segments", ["session_id"])
    op.create_index("ix_transcript_session_created", "session_transcript_segments", ["session_id", "created_at"])

    op.create_table(
        "candidate_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_concepts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transcript_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("session_transcript_segments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("polarity", sa.String(16), nullable=False, server_default="neutral"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="ck_candidate_evidence_confidence"),
    )
    op.create_index("ix_candidate_evidence_user_id", "candidate_evidence", ["user_id"])
    op.create_index("ix_candidate_evidence_project_id", "candidate_evidence", ["project_id"])
    op.create_index("ix_candidate_evidence_session_id", "candidate_evidence", ["session_id"])
    op.create_index("ix_candidate_evidence_concept_id", "candidate_evidence", ["concept_id"])
    op.create_index("ix_candidate_evidence_transcript_segment_id", "candidate_evidence", ["transcript_segment_id"])
    op.create_index("ix_candidate_evidence_user_observed", "candidate_evidence", ["user_id", "observed_at"])
    op.create_index("ix_candidate_evidence_project_concept", "candidate_evidence", ["project_id", "concept_id"])


def downgrade() -> None:
    op.drop_table("candidate_evidence")
    op.drop_table("session_transcript_segments")
    op.drop_table("candidate_skill_profiles")
    op.drop_table("project_knowledge_concepts")
    op.drop_table("knowledge_concepts")
