"""Anonymous session token unit tests — no database required."""

from __future__ import annotations

import time

import pytest

from app.core.config import Settings
from app.core.security import (
    AuthError,
    create_anonymous_session_id,
    verify_anonymous_session_id,
)


def test_anonymous_session_roundtrip() -> None:
    settings = Settings(anonymous_session_secret="unit-test-secret")
    session_id = create_anonymous_session_id(settings)
    assert verify_anonymous_session_id(session_id, settings) == session_id


def test_anonymous_session_rejects_tampering() -> None:
    settings = Settings(anonymous_session_secret="unit-test-secret")
    session_id = create_anonymous_session_id(settings)
    bad = session_id[:-4] + "dead"
    with pytest.raises(AuthError):
        verify_anonymous_session_id(bad, settings)


def test_anonymous_session_rejects_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(anonymous_session_secret="unit-test-secret", anonymous_session_ttl_days=1)
    # Force expiry in the past by mocking time during creation then advancing
    past = int(time.time()) - 10
    monkeypatch.setattr("app.core.security.time.time", lambda: past)
    session_id = create_anonymous_session_id(settings)
    monkeypatch.setattr("app.core.security.time.time", lambda: past + 86_400 * 2)
    with pytest.raises(AuthError, match="expired"):
        verify_anonymous_session_id(session_id, settings)
