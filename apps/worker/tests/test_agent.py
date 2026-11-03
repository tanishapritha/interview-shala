"""Unit tests for worker room identity and interview context."""

from uuid import UUID

import pytest

from src.agent import build_instructions, session_id_from_room


def test_session_id_is_derived_from_expected_room_name() -> None:
    session_id = UUID("9e7b7cc0-65f8-4c8c-bb6d-9b3a1a2f7d91")

    assert session_id_from_room(f"interview-shala-{session_id}") == session_id


@pytest.mark.parametrize("room_name", ["other-room", "interview-shala-not-a-uuid", ""])
def test_worker_rejects_rooms_outside_interview_shala_namespace(room_name: str) -> None:
    with pytest.raises(ValueError):
        session_id_from_room(room_name)


def test_interview_prompt_uses_session_context_and_safety_rules() -> None:
    prompt = build_instructions(
        {
            "company": "Acme",
            "role": "Mechanical Design Engineer",
            "round_type": "technical",
            "job_description": "Design braking systems.",
        }
    )

    assert "Acme" in prompt
    assert "Mechanical Design Engineer" in prompt
    assert "Design braking systems." in prompt
    assert "Do not claim to evaluate or score" in prompt
