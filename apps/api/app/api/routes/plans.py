"""Preparation plan and task routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession, RequireIdentity
from app.models.plan import PreparationPlan
from app.models.project import InterviewProject
from app.schemas.plan import PreparationPlanResponse, PreparationTaskResponse, PreparationTaskUpdate
from app.services.ownership import ownership_filter
from app.services.readiness import recompute_project_metrics
from app.services.serializers import plan_to_response, task_to_response

router = APIRouter()


async def _get_owned_plan(db: DbSession, auth, plan_id: UUID) -> PreparationPlan:
    stmt = (
        select(PreparationPlan)
        .join(InterviewProject, PreparationPlan.project_id == InterviewProject.id)
        .where(PreparationPlan.id == plan_id, ownership_filter(auth))
        .options(
            selectinload(PreparationPlan.rounds),
            selectinload(PreparationPlan.tasks),
            selectinload(PreparationPlan.project),
        )
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.get("/{plan_id}", response_model=PreparationPlanResponse)
async def get_plan(
    plan_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> PreparationPlanResponse:
    plan = await _get_owned_plan(db, auth, plan_id)
    return plan_to_response(plan)


@router.patch("/{plan_id}/tasks/{task_id}", response_model=PreparationTaskResponse)
async def update_task(
    plan_id: UUID,
    task_id: UUID,
    body: PreparationTaskUpdate,
    db: DbSession,
    auth: RequireIdentity,
) -> PreparationTaskResponse:
    plan = await _get_owned_plan(db, auth, plan_id)
    task = next((t for t in plan.tasks if t.id == task_id), None)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)
    await db.flush()

    if plan.project:
        await recompute_project_metrics(db, plan.project)

    return task_to_response(task)
