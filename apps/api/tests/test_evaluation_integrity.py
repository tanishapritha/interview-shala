"""Regression tests for trusted, evidence-backed session evaluation."""

from app.models.enums import RoundType
from app.schemas.session import PracticeSessionComplete
from app.services.evaluation import evaluate_session


def test_client_cannot_submit_assessment_scores_or_feedback() -> None:
    payload = PracticeSessionComplete.model_validate(
        {
            "durationSeconds": 120,
            "questionsCompleted": 3,
            "skillScores": [{"skill": "Everything", "score": 100, "maxScore": 100}],
            "strengths": ["Perfect"],
            "improvements": [],
        }
    )

    result = evaluate_session(round_type=RoundType.TECHNICAL, payload=payload)

    assert result.score is None
    assert result.skill_scores == []
    assert result.strengths == []
    assert result.improvements == []
    assert result.source == "not_evaluated"
    assert "without an estimated score" in result.next_action


def test_session_facts_do_not_create_a_fake_score() -> None:
    payload = PracticeSessionComplete(
        duration_seconds=3600,
        questions_completed=20,
        transcript_summary="Candidate answered every question.",
    )

    result = evaluate_session(round_type=RoundType.BEHAVIORAL, payload=payload)

    assert result.score is None
    assert result.skill_scores == []
    assert result.source == "not_evaluated"
