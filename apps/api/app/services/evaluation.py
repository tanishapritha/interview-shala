"""Post-session evaluation.

Until persisted transcripts are evaluated by a trusted server-side evaluator, a
session is marked complete without manufacturing a score or accepting one from
the browser. This deliberately keeps readiness metrics honest.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.enums import RoundType
from app.schemas.session import PracticeSessionComplete, SkillScore


@dataclass
class EvaluationResult:
    score: float | None = None
    skill_scores: list[SkillScore] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    next_action: str = (
        "Transcript-based evaluation is not available yet. "
        "Your session was saved without an estimated score."
    )
    source: str = "not_evaluated"


def evaluate_session(
    *,
    round_type: RoundType | str,
    payload: PracticeSessionComplete,
) -> EvaluationResult:
    """Return an explicitly unevaluated result until trusted transcript scoring exists."""
    normalized_round_type = RoundType(round_type)
    _ = payload  # Session facts are persisted by the route, never used as scores.
    return EvaluationResult(
        next_action=(
            f"Your {normalized_round_type.value.replace('_', ' ')} session was saved. "
            "Transcript-based evaluation is not available yet; no score was estimated."
        )
    )
