"""Tests for ordered and drainable transcript writes."""

import asyncio
from uuid import uuid4

import pytest

from src.transcript_writer import TranscriptWriter


class RecordingAPI:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def append_transcript(self, session_id, **kwargs) -> None:
        await asyncio.sleep(0)
        self.calls.append({"session_id": session_id, **kwargs})


def test_writer_persists_turns_in_order_and_drains_on_close() -> None:
    async def scenario() -> None:
        api = RecordingAPI()
        session_id = uuid4()
        writer = TranscriptWriter(api, session_id, first_sequence=7)
        writer.submit("interviewer", "  First question  ", elapsed_ms=120)
        writer.submit("candidate", "My answer", elapsed_ms=245)
        await writer.close()

        assert [call["sequence_number"] for call in api.calls] == [7, 8]
        assert [call["speaker"] for call in api.calls] == ["interviewer", "candidate"]
        assert [call["text"] for call in api.calls] == ["First question", "My answer"]
        assert [call["elapsed_ms"] for call in api.calls] == [120, 245]

    asyncio.run(scenario())


def test_writer_ignores_empty_turns_and_rejects_writes_after_close() -> None:
    async def scenario() -> None:
        api = RecordingAPI()
        writer = TranscriptWriter(api, uuid4())
        writer.submit("candidate", "   ")
        await writer.close()
        assert api.calls == []
        with pytest.raises(RuntimeError, match="already closed"):
            writer.submit("candidate", "late answer")

    asyncio.run(scenario())


def test_writer_reports_persistence_failure_after_draining() -> None:
    class FailingAPI(RecordingAPI):
        async def append_transcript(self, session_id, **kwargs) -> None:
            raise RuntimeError("database unavailable")

    async def scenario() -> None:
        writer = TranscriptWriter(FailingAPI(), uuid4())
        writer.submit("candidate", "An answer")
        with pytest.raises(RuntimeError, match="failed to persist"):
            await writer.close()

    asyncio.run(scenario())


def test_writer_close_is_idempotent() -> None:
    async def scenario() -> None:
        api = RecordingAPI()
        writer = TranscriptWriter(api, uuid4())
        writer.submit("candidate", "Answer")
        await writer.close()
        await writer.close()
        assert len(api.calls) == 1

    asyncio.run(scenario())
