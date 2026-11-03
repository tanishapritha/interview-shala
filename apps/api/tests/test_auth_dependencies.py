"""Authentication and ownership boundary tests."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.core.deps import AuthContext, require_identity
from app.models.project import InterviewProject
from app.models.user import User
from app.services.ownership import ownership_filter


@pytest.mark.asyncio
async def test_candidate_data_requires_clerk_identity() -> None:
    anonymous_context = AuthContext(anonymous_session_id="valid-anonymous-token")

    with pytest.raises(HTTPException) as exc_info:
        await require_identity(anonymous_context)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Clerk authentication required"


@pytest.mark.asyncio
async def test_candidate_data_accepts_clerk_user() -> None:
    user = User(clerk_id="user_test_candidate")
    context = AuthContext(user=user)

    resolved = await require_identity(context)

    assert resolved.user is user


def test_authenticated_ownership_does_not_include_anonymous_token() -> None:
    user = User(clerk_id="user_test_candidate")
    context = AuthContext(
        user=user,
        anonymous_session_id="another-candidates-anonymous-token",
    )

    statement = select(InterviewProject).where(ownership_filter(context))
    sql = str(statement.compile(dialect=postgresql.dialect()))

    assert "interview_projects.user_id" in sql
    assert "anonymous_session_id" not in sql
