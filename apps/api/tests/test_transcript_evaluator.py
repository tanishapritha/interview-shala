from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.transcript_evaluator import EvaluationUnavailable, validate_evaluation


def segment(speaker: str, text: str):
    return SimpleNamespace(id=uuid4(), speaker=speaker, is_final=True, text=text)


def test_accepts_exact_quote_from_candidate_segment():
    candidate = segment("candidate", "I used a hash map to reduce lookup time.")
    raw = {
        "skills": [{
            "name": "Data structures",
            "score": 82,
            "confidence": 0.9,
            "rationale": "Explained a relevant optimisation.",
            "observations": [{
                "segment_id": str(candidate.id),
                "quote": "used a hash map",
                "polarity": "positive",
                "evidence_type": "technical_reasoning",
                "explanation": "Named a suitable data structure.",
                "confidence": 0.9,
            }],
        }],
        "next_action": "Practise complexity analysis.",
    }

    result = validate_evaluation(raw, [candidate])

    assert result.score == 82
    assert result.skills[0].observations[0].segment_id == candidate.id
    assert result.next_action == "Practise complexity analysis."


def test_rejects_fabricated_quote_and_interviewer_segment():
    candidate = segment("candidate", "I used a list.")
    interviewer = segment("interviewer", "Explain hash maps.")
    raw = {
        "skills": [{
            "name": "Data structures",
            "score": 95,
            "confidence": 1.0,
            "rationale": "Strong answer.",
            "observations": [
                {
                    "segment_id": str(candidate.id),
                    "quote": "I used a balanced tree",
                    "polarity": "positive",
                    "confidence": 1.0,
                },
                {
                    "segment_id": str(interviewer.id),
                    "quote": "Explain hash maps.",
                    "polarity": "positive",
                    "confidence": 1.0,
                },
            ],
        }]
    }

    with pytest.raises(EvaluationUnavailable):
        validate_evaluation(raw, [candidate, interviewer])


def test_rejects_invalid_score_even_with_valid_quote():
    candidate = segment("candidate", "I used a list.")
    raw = {
        "skills": [{
            "name": "Data structures",
            "score": 101,
            "confidence": 1.0,
            "observations": [{
                "segment_id": str(candidate.id),
                "quote": "used a list",
                "polarity": "positive",
                "confidence": 1.0,
            }],
        }]
    }

    with pytest.raises(EvaluationUnavailable):
        validate_evaluation(raw, [candidate])


def test_ignores_interim_candidate_transcript():
    interim = SimpleNamespace(id=uuid4(), speaker="candidate", is_final=False, text="draft")
    raw = {
        "skills": [{
            "name": "Communication",
            "score": 80,
            "confidence": 0.8,
            "observations": [{
                "segment_id": str(interim.id),
                "quote": "draft",
                "polarity": "positive",
                "confidence": 0.8,
            }],
        }]
    }

    with pytest.raises(EvaluationUnavailable):
        validate_evaluation(raw, [interim])
