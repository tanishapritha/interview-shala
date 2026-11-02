"""Post-session evaluation — heuristic scoring with optional LLM polish."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.core.config import Settings, get_settings
from app.models.enums import RoundType
from app.schemas.session import PracticeSessionComplete, SkillScore

logger = logging.getLogger(__name__)


DEFAULT_SKILLS_BY_ROUND: dict[RoundType, list[str]] = {
    RoundType.TECHNICAL: ["Technical depth", "Clarity", "Problem solving"],
    RoundType.DSA: ["Algorithmic thinking", "Code correctness", "Communication"],
    RoundType.SYSTEM_DESIGN: ["Architecture", "Trade-off reasoning", "Scalability"],
    RoundType.PROJECT: ["Ownership narrative", "Impact articulation", "Technical decisions"],
    RoundType.BEHAVIORAL: ["STAR structure", "Self-awareness", "Collaboration"],
    RoundType.HR: ["Motivation fit", "Conciseness", "Company research"],
}


@dataclass
class EvaluationResult:
    score: float
    skill_scores: list[SkillScore] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    next_action: str = ""
    source: str = "heuristic"


def evaluate_session(
    *,
    round_type: RoundType | str,
    payload: PracticeSessionComplete,
    settings: Settings | None = None,
) -> EvaluationResult:
    """
    Evaluate a completed practice session.

    Uses client-provided skill scores when present; otherwise applies heuristics.
    Does not invent a successful LLM evaluation when keys are missing.
    """
    cfg = settings or get_settings()
    rt = RoundType(round_type) if not isinstance(round_type, RoundType) else round_type

    if payload.skill_scores:
        skill_scores = payload.skill_scores
    else:
        skills = DEFAULT_SKILLS_BY_ROUND.get(rt, ["Overall performance"])
        # Neutral baseline — client didn't send scores; don't pretend we heard audio
        base = 55.0
        if payload.questions_completed:
            base = min(85.0, 45.0 + payload.questions_completed * 5.0)
        if payload.duration_seconds and payload.duration_seconds < 60:
            base = max(35.0, base - 15.0)
        skill_scores = [SkillScore(skill=s, score=base, max_score=100.0) for s in skills]

    overall = sum(s.score for s in skill_scores) / len(skill_scores) if skill_scores else 0.0

    strengths = list(payload.strengths or [])
    improvements = list(payload.improvements or [])

    if not strengths:
        top = sorted(skill_scores, key=lambda s: s.score, reverse=True)[:2]
        strengths = [f"Relative strength in {s.skill}" for s in top if s.score >= 60] or [
            "Completed a full practice pass"
        ]

    if not improvements:
        weak = sorted(skill_scores, key=lambda s: s.score)[:2]
        improvements = [
            f"Improve {s.skill} with a focused drill"
            for s in weak
            if s.score < 75
        ] or ["Add more concrete examples in answers"]

    next_action = (
        f"Schedule another {rt.value.replace('_', ' ')} voice session and "
        f"focus on: {improvements[0]}"
    )

    # Optional LLM enrichment is intentionally not required; heuristic is authoritative
    # when audio/transcript evaluation pipelines are not yet wired.
    _ = cfg  # reserved for future LLM post-eval when transcript pipeline exists

    return EvaluationResult(
        score=round(overall, 1),
        skill_scores=skill_scores,
        strengths=strengths,
        improvements=improvements,
        next_action=next_action,
        source="heuristic",
    )
