"""Helpers for project ownership checks (Clerk user vs anonymous session)."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import AuthContext
from app.models.plan import PreparationPlan
from app.models.project import InterviewProject
from app.models.session import PracticeSession


def ownership_filter(auth: AuthContext):
    """SQLAlchemy filter clause matching the caller's owned projects."""
    clauses = []
    if auth.user_id is not None:
        # An authenticated identity always takes precedence. Never widen its
        # access by also accepting an anonymous bearer token on the same request.
        clauses.append(InterviewProject.user_id == auth.user_id)
    elif auth.anonymous_session_id is not None:
        clauses.append(InterviewProject.anonymous_session_id == auth.anonymous_session_id)
    if not clauses:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return or_(*clauses)


async def get_owned_project(
    db: AsyncSession,
    auth: AuthContext,
    project_id: UUID,
    *,
    load_plan: bool = False,
) -> InterviewProject:
    stmt = select(InterviewProject).where(
        InterviewProject.id == project_id,
        ownership_filter(auth),
    )
    if load_plan:
        stmt = stmt.options(
            selectinload(InterviewProject.plan).selectinload(PreparationPlan.rounds),
            selectinload(InterviewProject.plan).selectinload(PreparationPlan.tasks),
        )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def get_owned_session(
    db: AsyncSession,
    auth: AuthContext,
    session_id: UUID,
) -> PracticeSession:
    stmt = (
        select(PracticeSession)
        .join(InterviewProject, PracticeSession.project_id == InterviewProject.id)
        .where(PracticeSession.id == session_id, ownership_filter(auth))
        .options(selectinload(PracticeSession.skill_assessments))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def apply_owner_fields(project: InterviewProject, auth: AuthContext) -> None:
    """Stamp user_id / anonymous_session_id on a new project."""
    if auth.user_id is not None:
        project.user_id = auth.user_id
    if auth.anonymous_session_id is not None and project.user_id is None:
        project.anonymous_session_id = auth.anonymous_session_id
    elif auth.anonymous_session_id is not None and project.user_id is not None:
        # Authenticated user still may send anonymous header during migrate window
        project.anonymous_session_id = None
