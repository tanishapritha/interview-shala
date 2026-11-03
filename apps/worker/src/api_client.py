"""Authenticated API client for worker-only session context and transcript writes."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import httpx


class InterviewShalaAPI:
    def __init__(self, base_url: str, worker_secret: str, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"X-Worker-Secret": worker_secret},
        )

    async def get_session(self, session_id: UUID) -> dict[str, Any]:
        response = await self._client.get(f"/api/v1/internal/worker/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    async def append_transcript(
        self,
        session_id: UUID,
        *,
        sequence_number: int,
        speaker: str,
        text: str,
        elapsed_ms: int,
    ) -> None:
        payload = [
            {
                "sequence_number": sequence_number,
                "speaker": speaker,
                "text": text,
                "elapsed_ms": elapsed_ms,
                "is_final": True,
            }
        ]
        for attempt in range(3):
            try:
                response = await self._client.post(
                    f"/api/v1/internal/worker/sessions/{session_id}/transcript-segments",
                    json=payload,
                )
                response.raise_for_status()
                return
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                retryable = isinstance(exc, httpx.TransportError) or (
                    exc.response is not None and exc.response.status_code >= 500
                )
                if not retryable or attempt == 2:
                    raise
                await asyncio.sleep(0.25 * (2**attempt))

    async def aclose(self) -> None:
        await self._client.aclose()
