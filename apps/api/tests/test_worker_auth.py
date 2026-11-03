"""Tests for private worker authentication."""

import pytest
from fastapi import HTTPException

from app.api.routes.worker import require_worker_secret
from app.core.config import Settings


@pytest.mark.asyncio
async def test_worker_endpoint_rejects_missing_configured_secret() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_worker_secret(
            x_worker_secret="anything",
            settings=Settings(worker_shared_secret=None),
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_worker_endpoint_rejects_incorrect_secret() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_worker_secret(
            x_worker_secret="wrong",
            settings=Settings(worker_shared_secret="correct"),
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_worker_endpoint_accepts_matching_secret() -> None:
    result = await require_worker_secret(
        x_worker_secret="correct",
        settings=Settings(worker_shared_secret="correct"),
    )
    assert result is None
