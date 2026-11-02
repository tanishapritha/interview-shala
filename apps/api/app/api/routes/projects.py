"""Interview project CRUD and quick-start."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession, RequireIdentity
from app.models.plan import PreparationPlan, PreparationRound, PreparationTask
from app.models.project import InterviewProject
from app.schemas.plan import PreparationPlanResponse
from app.schemas.project import (
    InterviewProjectCreate,
    InterviewProjectResponse,
    InterviewProjectUpdate,
    QuickStartPayload,
    QuickStartResponse,
)
from app.services.ownership import apply_owner_fields, get_owned_project, ownership_filter
from app.services.planner import generate_preparation_plan
from app.services.serializers import plan_to_response, project_to_response

router = APIRouter()


async def _persist_plan(
    db: DbSession,
    project: InterviewProject,
    planned,
) -> PreparationPlan:
    plan = PreparationPlan(project_id=project.id, summary=planned.summary)
    db.add(plan)
    await db.flush()

    for rnd in planned.rounds:
        db.add(
            PreparationRound(
                plan_id=plan.id,
                name=rnd.name,
                round_type=rnd.round_type,
                priority=rnd.priority,
                topics=rnd.topics,
                question_count=rnd.question_count,
                description=rnd.description,
            )
        )
    for task in planned.tasks:
        db.add(
            PreparationTask(
                plan_id=plan.id,
                title=task.title,
                description=task.description,
                round_type=task.round_type,
                priority=task.priority,
                estimated_minutes=task.estimated_minutes,
                is_today=task.is_today,
                due_date_offset_days=task.due_date_offset_days,
            )
        )
    await db.flush()

    result = await db.execute(
        select(PreparationPlan)
        .where(PreparationPlan.id == plan.id)
        .options(
            selectinload(PreparationPlan.rounds),
            selectinload(PreparationPlan.tasks),
        )
    )
    return result.scalar_one()


@router.get("", response_model=list[InterviewProjectResponse])
async def list_projects(db: DbSession, auth: RequireIdentity) -> list[InterviewProjectResponse]:
    result = await db.execute(
        select(InterviewProject)
        .where(ownership_filter(auth))
        .order_by(InterviewProject.updated_at.desc())
    )
    return [project_to_response(p) for p in result.scalars().all()]


@router.post("", response_model=InterviewProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: InterviewProjectCreate,
    db: DbSession,
    auth: RequireIdentity,
) -> InterviewProjectResponse:
    project = InterviewProject(**body.model_dump())
    apply_owner_fields(project, auth)
    db.add(project)
    await db.flush()
    return project_to_response(project)


@router.post(
    "/quick-start",
    response_model=QuickStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def quick_start(
    body: QuickStartPayload,
    db: DbSession,
    auth: RequireIdentity,
) -> QuickStartResponse:
    project = InterviewProject(
        company=body.company,
        role=body.role,
        job_description=body.job_description,
        company_url=body.company_url,
        interview_date=body.interview_date,
        additional_context=body.additional_context,
    )
    apply_owner_fields(project, auth)
    db.add(project)
    await db.flush()

    planned = await generate_preparation_plan(
        company=body.company,
        role=body.role,
        job_description=body.job_description,
        interview_date=body.interview_date,
        company_url=body.company_url,
        additional_context=body.additional_context,
    )
    plan = await _persist_plan(db, project, planned)
    return QuickStartResponse(
        project=project_to_response(project),
        plan=plan_to_response(plan),
    )


@router.get("/{project_id}", response_model=InterviewProjectResponse)
async def get_project(
    project_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> InterviewProjectResponse:
    project = await get_owned_project(db, auth, project_id)
    return project_to_response(project)


@router.patch("/{project_id}", response_model=InterviewProjectResponse)
async def update_project(
    project_id: UUID,
    body: InterviewProjectUpdate,
    db: DbSession,
    auth: RequireIdentity,
) -> InterviewProjectResponse:
    project = await get_owned_project(db, auth, project_id)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(project, key, value)
    await db.flush()
    return project_to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> None:
    project = await get_owned_project(db, auth, project_id)
    await db.delete(project)
    await db.flush()


@router.get("/{project_id}/plan", response_model=PreparationPlanResponse)
async def get_project_plan(
    project_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> PreparationPlanResponse:
    project = await get_owned_project(db, auth, project_id, load_plan=True)
    if project.plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan_to_response(project.plan)
