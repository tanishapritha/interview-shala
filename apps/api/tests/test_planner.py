"""Template planner unit tests — no database / LLM required."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import RoundType
from app.services.planner import build_template_plan, generate_preparation_plan
from app.core.config import Settings


def test_build_template_plan_includes_core_rounds() -> None:
    plan = build_template_plan(company="Acme Corp", role="Backend Engineer")
    assert plan.source == "template"
    assert "Acme Corp" in plan.summary
    assert "Backend Engineer" in plan.summary

    types = {r.round_type for r in plan.rounds}
    assert RoundType.TECHNICAL in types
    assert RoundType.HR in types
    assert RoundType.BEHAVIORAL in types
    assert RoundType.PROJECT in types
    assert RoundType.SYSTEM_DESIGN in types

    today = [t for t in plan.tasks if t.is_today]
    assert len(today) >= 3
    assert all(t.title and t.estimated_minutes for t in plan.tasks)


def test_frontend_role_gets_frontend_topics() -> None:
    plan = build_template_plan(company="Pixel", role="Senior Frontend Engineer")
    technical = next(r for r in plan.rounds if r.round_type == RoundType.TECHNICAL)
    joined = " ".join(technical.topics).lower()
    assert "react" in joined or "javascript" in joined or "typescript" in joined


def test_job_description_keyword_boost() -> None:
    plan = build_template_plan(
        company="CloudCo",
        role="Platform Engineer",
        job_description="We need strong Kubernetes and AWS experience with Kafka pipelines.",
    )
    technical = next(r for r in plan.rounds if r.round_type == RoundType.TECHNICAL)
    topics = set(technical.topics)
    assert "Kubernetes" in topics or "AWS" in topics or "Kafka" in topics


def test_intensive_mode_near_interview() -> None:
    tomorrow = date.today() + timedelta(days=2)
    plan = build_template_plan(
        company="FastHire",
        role="Full Stack Developer",
        interview_date=tomorrow,
    )
    assert "intensive" in plan.summary.lower()
    today_count = sum(1 for t in plan.tasks if t.is_today)
    assert today_count >= 3


@pytest.mark.asyncio
async def test_generate_without_llm_uses_template() -> None:
    settings = Settings(
        groq_api_key=None,
        openrouter_api_key=None,
        anonymous_session_secret="test-secret",
    )
    plan = await generate_preparation_plan(
        company="NoLLM Inc",
        role="Data Engineer",
        settings=settings,
    )
    assert plan.source == "template"
    assert len(plan.rounds) >= 5
    assert len(plan.tasks) >= 5
