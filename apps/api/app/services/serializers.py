"""ORM → response schema mappers."""

from __future__ import annotations

from app.models.plan import PreparationPlan, PreparationRound, PreparationTask
from app.models.project import InterviewProject
from app.models.session import PracticeSession, SkillAssessment
from app.models.weakness import Weakness
from app.schemas.plan import (
    PreparationPlanResponse,
    PreparationRoundResponse,
    PreparationTaskResponse,
)
from app.schemas.project import InterviewProjectResponse
from app.schemas.session import PracticeSessionResponse, SkillScore
from app.schemas.weakness import WeaknessResponse


def project_to_response(project: InterviewProject) -> InterviewProjectResponse:
    return InterviewProjectResponse.model_validate(project)


def task_to_response(task: PreparationTask) -> PreparationTaskResponse:
    return PreparationTaskResponse.model_validate(task)


def round_to_response(round_: PreparationRound) -> PreparationRoundResponse:
    return PreparationRoundResponse.model_validate(round_)


def plan_to_response(plan: PreparationPlan) -> PreparationPlanResponse:
    tasks = [task_to_response(t) for t in plan.tasks]
    today = [task_to_response(t) for t in plan.tasks if t.is_today]
    return PreparationPlanResponse(
        id=plan.id,
        project_id=plan.project_id,
        summary=plan.summary,
        rounds=[round_to_response(r) for r in plan.rounds],
        tasks=tasks,
        today_tasks=today,
    )


def session_to_response(session: PracticeSession) -> PracticeSessionResponse:
    skill_scores = [
        SkillScore(skill=s.skill, score=s.score, max_score=s.max_score)
        for s in (session.skill_assessments or [])
    ]
    return PracticeSessionResponse(
        id=session.id,
        project_id=session.project_id,
        round_id=session.round_id,
        round_type=session.round_type,
        status=session.status,
        score=session.score,
        duration_seconds=session.duration_seconds,
        questions_completed=session.questions_completed,
        skill_scores=skill_scores,
        strengths=list(session.strengths or []),
        improvements=list(session.improvements or []),
        next_action=session.next_action,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


def weakness_to_response(weakness: Weakness) -> WeaknessResponse:
    evidence = [e.evidence for e in (weakness.evidence_items or [])]
    return WeaknessResponse(
        id=weakness.id,
        skill=weakness.skill,
        severity=weakness.severity,
        observation_count=weakness.observation_count,
        summary=weakness.summary,
        evidence=evidence,
        recommended_exercise=weakness.recommended_exercise,
        recent_progress=weakness.recent_progress,
        updated_at=weakness.updated_at,
    )
