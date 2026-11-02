"""Weakness listing routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import DbSession, RequireIdentity
from app.schemas.weakness import WeaknessResponse
from app.services.ownership import get_owned_project
from app.services.serializers import weakness_to_response
from app.services.weakness_tracker import list_project_weaknesses

router = APIRouter()


@router.get("/project/{project_id}", response_model=list[WeaknessResponse])
async def list_weaknesses(
    project_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> list[WeaknessResponse]:
    await get_owned_project(db, auth, project_id)
    weaknesses = await list_project_weaknesses(db, project_id)
    return [weakness_to_response(w) for w in weaknesses]
