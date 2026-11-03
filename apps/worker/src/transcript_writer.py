"""Ordered, drainable transcript persistence for a LiveKit job."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from src.api_client import InterviewShalaAPI

logger = logging.getLogger("interview_shala.worker.transcript")


@dataclass(frozen=True, slots=True)
class TranscriptTurn:
    speaker: str
    text: str
    elapsed_ms: int


class TranscriptWriter:
    """Serialize transcript writes and drain every queued turn before shutdown."""

    def __init__(
        self,
        api: InterviewShalaAPI,
        session_id: UUID,
        *,
        first_sequence: int = 0,
    ) -> None:
        self._api = api
        self._session_id = session_id
        self._next_sequence = first_sequence
        self._queue: asyncio.Queue[TranscriptTurn | None] = asyncio.Queue()
        self._failures: list[Exception] = []
        self._closed = False
        self._task = asyncio.create_task(self._run())

    def submit(self, speaker: str, text: str, *, elapsed_ms: int = 0) -> None:
        if self._closed:
            raise RuntimeError("Transcript writer is already closed")
        normalized = text.strip()
        if normalized:
            self._queue.put_nowait(TranscriptTurn(speaker=speaker, text=normalized, elapsed_ms=elapsed_ms))

    async def _run(self) -> None:
        while True:
            turn = await self._queue.get()
            try:
                if turn is None:
                    return
                sequence = self._next_sequence
                try:
                    await self._api.append_transcript(
                        self._session_id,
                        sequence_number=sequence,
                        speaker=turn.speaker,
                        text=turn.text,
                        elapsed_ms=turn.elapsed_ms,
                    )
                except Exception as exc:
                    self._failures.append(exc)
                    logger.exception(
                        "Transcript turn could not be persisted",
                        extra={
                            "session_id": str(self._session_id),
                            "sequence_number": sequence,
                        },
                    )
                finally:
                    self._next_sequence += 1
            finally:
                self._queue.task_done()

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.join()
        self._queue.put_nowait(None)
        await self._task
        if self._failures:
            raise RuntimeError(
                f"{len(self._failures)} transcript turn(s) failed to persist "
                f"for session {self._session_id}"
            ) from self._failures[0]
