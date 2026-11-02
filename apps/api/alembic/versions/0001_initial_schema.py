"""Initial schema for Interview Shala

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-02

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("clerk_id", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_clerk_id", "users", ["clerk_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "interview_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("anonymous_session_id", sa.String(length=512), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("company_url", sa.String(length=2048), nullable=True),
        sa.Column("interview_date", sa.Date(), nullable=True),
        sa.Column("additional_context", sa.Text(), nullable=True),
        sa.Column("readiness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_interview_projects_user_id", "interview_projects", ["user_id"])
    op.create_index("ix_interview_projects_anonymous_session_id", "interview_projects", ["anonymous_session_id"])

    op.create_table(
        "preparation_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("ix_preparation_plans_project_id", "preparation_plans", ["project_id"], unique=True)

    op.create_table(
        "preparation_rounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("preparation_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("round_type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("topics", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_preparation_rounds_plan_id", "preparation_rounds", ["plan_id"])

    op.create_table(
        "preparation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("preparation_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("round_type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("due_date_offset_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_today", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_preparation_tasks_plan_id", "preparation_tasks", ["plan_id"])

    op.create_table(
        "practice_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("preparation_rounds.id", ondelete="SET NULL"), nullable=True),
        sa.Column("round_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("questions_completed", sa.Integer(), nullable=True),
        sa.Column("strengths", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("improvements", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("livekit_room_name", sa.String(length=255), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_practice_sessions_project_id", "practice_sessions", ["project_id"])
    op.create_index("ix_practice_sessions_round_id", "practice_sessions", ["round_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("round_type", sa.String(length=64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expected_topics", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_interview_questions_session_id", "interview_questions", ["session_id"])
    op.create_index("ix_interview_questions_project_id", "interview_questions", ["project_id"])

    op.create_table(
        "interview_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.String(length=2048), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_interview_answers_question_id", "interview_answers", ["question_id"])
    op.create_index("ix_interview_answers_session_id", "interview_answers", ["session_id"])

    op.create_table(
        "skill_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("skill", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="100"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_skill_assessments_session_id", "skill_assessments", ["session_id"])
    op.create_index("ix_skill_assessments_project_id", "skill_assessments", ["project_id"])

    op.create_table(
        "weaknesses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=64), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("recommended_exercise", sa.Text(), nullable=False, server_default=""),
        sa.Column("recent_progress", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_weaknesses_project_id", "weaknesses", ["project_id"])

    op.create_table(
        "weakness_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("weakness_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("weaknesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_weakness_evidence_weakness_id", "weakness_evidence", ["weakness_id"])
    op.create_index("ix_weakness_evidence_session_id", "weakness_evidence", ["session_id"])

    op.create_table(
        "provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("encrypted_secret", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_provider_configs_user_id", "provider_configs", ["user_id"])

    op.create_table(
        "session_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_session_events_session_id", "session_events", ["session_id"])


def downgrade() -> None:
    op.drop_table("session_events")
    op.drop_table("provider_configs")
    op.drop_table("weakness_evidence")
    op.drop_table("weaknesses")
    op.drop_table("skill_assessments")
    op.drop_table("interview_answers")
    op.drop_table("interview_questions")
    op.drop_table("practice_sessions")
    op.drop_table("preparation_tasks")
    op.drop_table("preparation_rounds")
    op.drop_table("preparation_plans")
    op.drop_table("interview_projects")
    op.drop_table("users")
