"""LiveKit access token generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class LiveKitCredentials:
    token: str
    room_name: str
    livekit_url: str
    session_id: UUID


def create_session_token(
    *,
    session_id: UUID,
    identity: str,
    room_name: str | None = None,
    settings: Settings | None = None,
    ttl_hours: int = 2,
) -> LiveKitCredentials:
    """
    Create a LiveKit participant token for a practice session.

    Raises HTTP 503 when LiveKit is not configured — never returns a fake token.
    """
    cfg = settings or get_settings()
    if not cfg.livekit_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "LiveKit is not configured. Set LIVEKIT_API_KEY, LIVEKIT_API_SECRET, "
                "and LIVEKIT_URL to enable voice sessions."
            ),
        )

    try:
        from livekit.api import AccessToken, VideoGrants
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="livekit-api package is not installed on this server",
        ) from exc

    room = room_name or f"interview-shala-{session_id}"
    grants = VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
    token = (
        AccessToken(cfg.livekit_api_key, cfg.livekit_api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(grants)
        .with_ttl(timedelta(hours=ttl_hours))
        .to_jwt()
    )

    assert cfg.livekit_url is not None
    return LiveKitCredentials(
        token=token,
        room_name=room,
        livekit_url=cfg.livekit_url,
        session_id=session_id,
    )
