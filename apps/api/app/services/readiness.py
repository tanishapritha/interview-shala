"""Compute project readiness and progress from plan + sessions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import SessionStatus
from app.models.plan import PreparationPlan
from app.models.project import InterviewProject
from app.models.session import PracticeSession


async def recompute_project_metrics(db: AsyncSession, project: InterviewProject) -> InterviewProject:
    """Update readiness_score and progress_percent on the project."""
    plan: PreparationPlan | None = project.plan
    if plan is None:
        result = await db.execute(
            select(PreparationPlan)
            .where(PreparationPlan.project_id == project.id)
            .options(
                selectinload(PreparationPlan.tasks),
                selectinload(PreparationPlan.rounds),
            )
        )
        plan = result.scalar_one_or_none()

    tasks = list(plan.tasks) if plan else []
    completed_tasks = sum(1 for t in tasks if t.completed)
    task_progress = (completed_tasks / len(tasks) * 100.0) if tasks else 0.0

    sessions_result = await db.execute(
        select(PracticeSession).where(PracticeSession.project_id == project.id)
    )
    sessions = list(sessions_result.scalars().all())
    completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]
    session_bonus = min(len(completed_sessions) * 8.0, 40.0)

    avg_score = 0.0
    if completed_sessions:
        scored = [s.score for s in completed_sessions if s.score is not None]
        if scored:
            avg_score = sum(scored) / len(scored)

    # Weighted readiness: task completion, practice volume, session quality
    readiness = min(
        100.0,
        (task_progress * 0.45) + session_bonus + (avg_score * 0.15),
    )
    progress = int(round(min(100.0, task_progress * 0.7 + min(len(completed_sessions) * 10, 30))))

    project.readiness_score = round(readiness, 1)
    project.progress_percent = progress

    if plan and plan.rounds:
        # Distribute crude round progress from related completed sessions
        by_type: dict[str, list[PracticeSession]] = {}
        for s in completed_sessions:
            by_type.setdefault(s.round_type, []).append(s)
        for rnd in plan.rounds:
            related = by_type.get(rnd.round_type, [])
            if related:
                scores = [s.score for s in related if s.score is not None]
                rnd.progress_percent = int(
                    min(100, 40 + len(related) * 20 + (sum(scores) / len(scores) * 0.2 if scores else 0))
                )
            else:
                # Tasks completed for this round type contribute a little
                round_tasks = [t for t in tasks if t.round_type == rnd.round_type]
                if round_tasks:
                    done = sum(1 for t in round_tasks if t.completed)
                    rnd.progress_percent = int(done / len(round_tasks) * 60)

    await db.flush()
    return project
