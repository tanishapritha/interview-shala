"""Clerk JWT verification and anonymous session tokens."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import Settings, get_settings


class AuthError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized") -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ClerkClaims:
    sub: str
    email: str | None = None
    raw: dict[str, Any] | None = None


_jwks_client: PyJWKClient | None = None
_jwks_client_url: str | None = None


def _get_jwks_client(settings: Settings) -> PyJWKClient:
    global _jwks_client, _jwks_client_url
    if not settings.clerk_jwks_url:
        raise AuthError("Clerk JWKS URL is not configured")
    if _jwks_client is None or _jwks_client_url != settings.clerk_jwks_url:
        _jwks_client = PyJWKClient(settings.clerk_jwks_url, cache_keys=True)
        _jwks_client_url = settings.clerk_jwks_url
    return _jwks_client


def verify_clerk_token(token: str, settings: Settings | None = None) -> ClerkClaims:
    """Validate a Clerk-issued Bearer JWT and return claims."""
    cfg = settings or get_settings()
    if not cfg.clerk_configured:
        raise AuthError("Clerk authentication is not configured on this server")

    try:
        client = _get_jwks_client(cfg)
        signing_key = client.get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "options": {"verify_aud": bool(cfg.clerk_audience)},
        }
        if cfg.clerk_audience:
            decode_kwargs["audience"] = cfg.clerk_audience
        issuer = cfg.clerk_issuer
        if not issuer and cfg.clerk_jwks_url:
            jwks_origin = urlsplit(cfg.clerk_jwks_url)
            issuer = f"{jwks_origin.scheme}://{jwks_origin.netloc}"
        if issuer:
            decode_kwargs["issuer"] = issuer

        payload = jwt.decode(token, signing_key.key, **decode_kwargs)
    except AuthError:
        raise
    except Exception as exc:  # noqa: BLE001 — map all JWT failures to AuthError
        raise AuthError("Invalid or expired authentication token") from exc

    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise AuthError("Token missing subject claim")

    email = payload.get("email")
    if not email:
        # Clerk often nests email under primary email address claim variants
        email = payload.get("primary_email_address") or payload.get("email_address")

    return ClerkClaims(sub=sub, email=email if isinstance(email, str) else None, raw=payload)


def create_anonymous_session_id(settings: Settings | None = None) -> str:
    """
    Create a signed anonymous session identifier.

    Format: `{uuid_hex}.{expiry_unix}.{signature}`
    """
    cfg = settings or get_settings()
    session_uuid = secrets.token_hex(16)
    expiry = int(time.time()) + cfg.anonymous_session_ttl_days * 86_400
    payload = f"{session_uuid}.{expiry}"
    signature = _sign(payload, cfg.anonymous_session_secret)
    return f"{payload}.{signature}"


def verify_anonymous_session_id(
    session_id: str,
    settings: Settings | None = None,
) -> str:
    """Validate signature + expiry; return the session id string on success."""
    cfg = settings or get_settings()
    parts = session_id.split(".")
    if len(parts) != 3:
        raise AuthError("Malformed anonymous session id")

    session_uuid, expiry_str, signature = parts
    try:
        expiry = int(expiry_str)
    except ValueError as exc:
        raise AuthError("Malformed anonymous session id") from exc

    if expiry < int(time.time()):
        raise AuthError("Anonymous session has expired")

    payload = f"{session_uuid}.{expiry_str}"
    expected = _sign(payload, cfg.anonymous_session_secret)
    if not hmac.compare_digest(expected, signature):
        raise AuthError("Invalid anonymous session signature")

    return session_id


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_for_storage(value: str) -> str:
    """Deterministic hash useful for indexing opaque session ids."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_uuid(value: str, *, field: str = "id") -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise AuthError(f"Invalid {field}") from exc


async def fetch_clerk_user_email(clerk_user_id: str, settings: Settings | None = None) -> str | None:
    """Optionally enrich user email via Clerk Backend API when secret key is set."""
    cfg = settings or get_settings()
    if not cfg.clerk_secret_key:
        return None

    url = f"https://api.clerk.com/v1/users/{clerk_user_id}"
    headers = {"Authorization": f"Bearer {cfg.clerk_secret_key}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return None
        data = response.json()
        emails = data.get("email_addresses") or []
        primary_id = data.get("primary_email_address_id")
        for item in emails:
            if item.get("id") == primary_id:
                return item.get("email_address")
        if emails:
            return emails[0].get("email_address")
    return None
