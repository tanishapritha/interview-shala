"""Contract tests for transcript API schemas and trust boundaries."""

import pytest
from pydantic import ValidationError

from app.schemas.transcript import TranscriptSegmentCreate


def test_transcript_segment_requires_supported_speaker_and_nonempty_text() -> None:
    segment = TranscriptSegmentCreate(
        sequence_number=0,
        speaker="candidate",
        text="Explain the design trade-off.",
        elapsed_ms=1200,
    )

    assert segment.sequence_number == 0
    assert segment.speaker == "candidate"


@pytest.mark.parametrize(
    "payload",
    [
        {"sequence_number": -1, "speaker": "candidate", "text": "answer"},
        {"sequence_number": 0, "speaker": "system", "text": "internal prompt"},
        {"sequence_number": 0, "speaker": "interviewer", "text": ""},
        {"sequence_number": 0, "speaker": "candidate", "text": "answer", "elapsed_ms": -1},
    ],
)
def test_transcript_segment_rejects_invalid_client_input(payload: dict) -> None:
    with pytest.raises(ValidationError):
        TranscriptSegmentCreate.model_validate(payload)


def test_transcript_segments_are_explicitly_client_supplied() -> None:
    assert TranscriptSegmentCreate.model_fields["speaker"].annotation
