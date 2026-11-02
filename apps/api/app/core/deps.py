"""FastAPI dependencies for auth and database access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import (
    AuthError,
    ClerkClaims,
    verify_anonymous_session_id,
    verify_clerk_token,
)
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@dataclass(slots=True)
class AuthContext:
    """Resolved caller identity — authenticated, anonymous, or both during migrate."""

    user: User | None = None
    clerk_claims: ClerkClaims | None = None
    anonymous_session_id: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None and self.user.clerk_id is not None

    @property
    def user_id(self) -> UUID | None:
        return self.user.id if self.user else None


async def get_optional_auth(
    db: DbSession,
    settings: AppSettings,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
    x_anonymous_session: Annotated[str | None, Header()] = None,
) -> AuthContext:
    """Resolve Clerk user and/or anonymous session without requiring either."""
    ctx = AuthContext()

    if credentials and credentials.credentials:
        try:
            claims = verify_clerk_token(credentials.credentials, settings)
        except AuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc

        ctx.clerk_claims = claims
        result = await db.execute(select(User).where(User.clerk_id == claims.sub))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(clerk_id=claims.sub, email=claims.email)
            db.add(user)
            await db.flush()
        elif claims.email and user.email != claims.email:
            user.email = claims.email
        ctx.user = user

    if x_anonymous_session:
        try:
            session_id = verify_anonymous_session_id(x_anonymous_session, settings)
        except AuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
        ctx.anonymous_session_id = session_id

    return ctx


async def require_identity(
    auth: Annotated[AuthContext, Depends(get_optional_auth)],
) -> AuthContext:
    """Require either a Clerk user or a valid anonymous session."""
    if auth.user is None and auth.anonymous_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: provide Bearer token or X-Anonymous-Session",
        )
    return auth


async def require_authenticated_user(
    auth: Annotated[AuthContext, Depends(get_optional_auth)],
) -> AuthContext:
    """Require a Clerk-authenticated user."""
    if auth.user is None or auth.user.clerk_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clerk authentication required",
        )
    return auth


OptionalAuth = Annotated[AuthContext, Depends(get_optional_auth)]
RequireIdentity = Annotated[AuthContext, Depends(require_identity)]
RequireUser = Annotated[AuthContext, Depends(require_authenticated_user)]
