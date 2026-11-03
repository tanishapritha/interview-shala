"""Anonymous auth and migration routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy import update

from app.core.config import get_settings
from app.core.deps import DbSession, RequireUser
from app.core.security import AuthError, create_anonymous_session_id, verify_anonymous_session_id
from app.models.project import InterviewProject
from app.schemas.auth import AnonymousSessionResponse, CurrentUserResponse, MigrateAnonymousRequest
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user(auth: RequireUser) -> CurrentUserResponse:
    """Return the authenticated candidate profile, creating it on first valid request."""
    assert auth.user is not None
    auth.user.last_login_at = datetime.now(timezone.utc)
    return CurrentUserResponse(
        id=auth.user.id,
        email=auth.user.email,
        display_name=auth.user.display_name,
        created_at=auth.user.created_at,
        last_login_at=auth.user.last_login_at,
    )


@router.post("/anonymous", response_model=AnonymousSessionResponse)
async def create_anonymous_session() -> AnonymousSessionResponse:
    settings = get_settings()
    session_id = create_anonymous_session_id(settings)
    return AnonymousSessionResponse(
        session_id=session_id,
        expires_in_days=settings.anonymous_session_ttl_days,
    )


@router.post("/migrate", response_model=MessageResponse)
async def migrate_anonymous_projects(
    db: DbSession,
    auth: RequireUser,
    body: MigrateAnonymousRequest | None = None,
    x_anonymous_session: str | None = Header(default=None),
) -> MessageResponse:
    """
    Attach anonymous-owned projects to the authenticated Clerk user.

    Accepts anonymous session via body.anonymousSessionId or X-Anonymous-Session header.
    """
    settings = get_settings()
    raw = (body.anonymous_session_id if body else None) or x_anonymous_session
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide anonymousSessionId in body or X-Anonymous-Session header",
        )

    try:
        session_id = verify_anonymous_session_id(raw, settings)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc

    assert auth.user is not None
    result = await db.execute(
        update(InterviewProject)
        .where(
            InterviewProject.anonymous_session_id == session_id,
            InterviewProject.user_id.is_(None),
        )
        .values(user_id=auth.user.id, anonymous_session_id=None)
        .returning(InterviewProject.id)
    )
    migrated_ids = list(result.scalars().all())
    await db.flush()

    return MessageResponse(
        message=f"Migrated {len(migrated_ids)} project(s) to your account",
        details={"projectIds": [str(i) for i in migrated_ids]},
    )
