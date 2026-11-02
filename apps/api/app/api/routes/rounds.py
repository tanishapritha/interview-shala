"""Preparation round routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession, RequireIdentity
from app.models.plan import PreparationPlan, PreparationRound
from app.models.project import InterviewProject
from app.schemas.plan import PreparationRoundResponse
from app.services.ownership import ownership_filter
from app.services.serializers import round_to_response

router = APIRouter()


@router.get("/by-project/{project_id}", response_model=list[PreparationRoundResponse])
async def list_rounds_for_project(
    project_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> list[PreparationRoundResponse]:
    stmt = (
        select(PreparationPlan)
        .join(InterviewProject, PreparationPlan.project_id == InterviewProject.id)
        .where(PreparationPlan.project_id == project_id, ownership_filter(auth))
        .options(selectinload(PreparationPlan.rounds))
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return [round_to_response(r) for r in plan.rounds]


@router.get("/{round_id}", response_model=PreparationRoundResponse)
async def get_round(
    round_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> PreparationRoundResponse:
    stmt = (
        select(PreparationRound)
        .join(PreparationPlan, PreparationRound.plan_id == PreparationPlan.id)
        .join(InterviewProject, PreparationPlan.project_id == InterviewProject.id)
        .where(PreparationRound.id == round_id, ownership_filter(auth))
    )
    result = await db.execute(stmt)
    round_ = result.scalar_one_or_none()
    if round_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")
    return round_to_response(round_)
