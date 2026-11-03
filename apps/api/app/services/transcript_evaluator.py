"""Evidence-grounded transcript evaluation.

A model score is accepted only when its supporting quote is an exact substring
of the final candidate segment identified by the model's segment_id.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.intelligence import CandidateEvidence, CandidateSkillProfile, SessionTranscriptSegment

logger = logging.getLogger(__name__)


class EvaluationUnavailable(RuntimeError):
    """Evaluation could not be completed with verifiable evidence."""


@dataclass(frozen=True)
class VerifiedObservation:
    segment_id: UUID
    skill: str
    polarity: str
    evidence_type: str
    quote: str
    explanation: str
    confidence: float


@dataclass(frozen=True)
class VerifiedSkill:
    name: str
    score: float
    confidence: float
    rationale: str
    observations: tuple[VerifiedObservation, ...]


@dataclass(frozen=True)
class TranscriptEvaluation:
    score: float
    strengths: tuple[str, ...]
    improvements: tuple[str, ...]
    next_action: str
    skills: tuple[VerifiedSkill, ...]


def _bounded_number(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if minimum <= number <= maximum else None


def validate_evaluation(raw: Any, segments: list[SessionTranscriptSegment]) -> TranscriptEvaluation:
    if not isinstance(raw, dict) or not isinstance(raw.get("skills"), list):
        raise EvaluationUnavailable("Evaluator returned an invalid response.")
    candidates = {
        str(segment.id): segment
        for segment in segments
        if segment.speaker == "candidate" and segment.is_final and segment.text.strip()
    }
    verified_skills: list[VerifiedSkill] = []
    for item in raw["skills"][:20]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()[:120]
        score = _bounded_number(item.get("score"), 0, 100)
        confidence = _bounded_number(item.get("confidence"), 0, 1)
        if not name or score is None or confidence is None:
            continue
        observations: list[VerifiedObservation] = []
        raw_observations = item.get("observations", [])
        if not isinstance(raw_observations, list):
            continue
        for observation in raw_observations[:20]:
            if not isinstance(observation, dict):
                continue
            segment_id = str(observation.get("segment_id", ""))
            source = candidates.get(segment_id)
            quote = observation.get("quote")
            polarity = observation.get("polarity")
            obs_confidence = _bounded_number(observation.get("confidence"), 0, 1)
            if (
                source is None
                or not isinstance(quote, str)
                or not quote.strip()
                or quote not in source.text
                or polarity not in {"positive", "negative", "neutral"}
                or obs_confidence is None
            ):
                continue
            try:
                parsed_id = UUID(segment_id)
            except ValueError:
                continue
            observations.append(VerifiedObservation(
                segment_id=parsed_id,
                skill=name,
                polarity=polarity,
                evidence_type=str(observation.get("evidence_type", "answer_quality"))[:64],
                quote=quote,
                explanation=str(observation.get("explanation", ""))[:1000],
                confidence=obs_confidence,
            ))
        if observations:
            verified_skills.append(VerifiedSkill(
                name=name,
                score=score,
                confidence=confidence,
                rationale=str(item.get("rationale", ""))[:1000],
                observations=tuple(observations),
            ))
    if not verified_skills:
        raise EvaluationUnavailable("No assessment could be tied to verified candidate speech.")
    total_weight = sum(skill.confidence for skill in verified_skills)
    overall = sum(skill.score * skill.confidence for skill in verified_skills) / max(total_weight, 0.001)
    strengths = tuple(dict.fromkeys(
        skill.rationale for skill in verified_skills if skill.score >= 70 and skill.rationale
    ))[:5]
    improvements = tuple(dict.fromkeys(
        skill.rationale for skill in verified_skills if skill.score < 70 and skill.rationale
    ))[:5]
    next_action = raw.get("next_action")
    if not isinstance(next_action, str) or not next_action.strip():
        next_action = "Practise the weakest assessed skill and review its cited evidence."
    return TranscriptEvaluation(
        score=round(overall, 1),
        strengths=strengths,
        improvements=improvements,
        next_action=next_action[:500],
        skills=tuple(verified_skills),
    )


async def evaluate_transcript(
    db: AsyncSession,
    *,
    session_id: UUID,
    project_id: UUID,
    user_id: UUID | None,
    segments: list[SessionTranscriptSegment],
) -> TranscriptEvaluation:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise EvaluationUnavailable("OpenRouter is not configured.")
    candidate_segments = [
        segment for segment in segments
        if segment.speaker == "candidate" and segment.is_final and segment.text.strip()
    ]
    if not candidate_segments:
        raise EvaluationUnavailable("No final candidate transcript is available.")

    prompt = {
        "task": (
            "Assess interview answer quality, technical correctness, reasoning, depth and communication. "
            "Only assess what the candidate actually said. Scores are 0-100; confidence is 0-1. "
            "Each observation must cite an exact substring from one candidate segment by segment_id. "
            "Never cite interviewer speech. Omit skills without direct evidence."
        ),
        "transcript": [
            {"segment_id": str(segment.id), "text": segment.text}
            for segment in candidate_segments
        ],
        "required_json_shape": {
            "skills": [{
                "name": "string", "score": 0, "confidence": 0.0, "rationale": "string",
                "observations": [{
                    "segment_id": "uuid", "quote": "exact substring",
                    "polarity": "positive|negative|neutral",
                    "evidence_type": "string", "explanation": "string", "confidence": 0.0,
                }],
            }],
            "next_action": "string",
        },
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openrouter_model,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": "Return only valid JSON. Be rigorous and evidence-bound."},
                        {"role": "user", "content": json.dumps(prompt)},
                    ],
                },
            )
            response.raise_for_status()
            raw_content = response.json()["choices"][0]["message"]["content"]
            raw = json.loads(raw_content)
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("Transcript evaluation provider failed: %s", exc)
        raise EvaluationUnavailable("Transcript evaluation is temporarily unavailable.") from exc

    evaluation = validate_evaluation(raw, segments)

    # Replace evidence from this session so a retried completion cannot double-count it.
    if user_id is not None:
        await db.execute(
            delete(CandidateEvidence).where(CandidateEvidence.session_id == session_id)
        )
        for skill in evaluation.skills:
            skill_key = "-".join(skill.name.lower().split())[:160]
            for observation in skill.observations:
                db.add(CandidateEvidence(
                    user_id=user_id,
                    project_id=project_id,
                    session_id=session_id,
                    transcript_segment_id=observation.segment_id,
                    evidence_type=observation.evidence_type,
                    polarity=observation.polarity,
                    content=observation.explanation or observation.quote,
                    confidence=observation.confidence,
                ))
            profile = await db.scalar(select(CandidateSkillProfile).where(
                CandidateSkillProfile.user_id == user_id,
                CandidateSkillProfile.skill_key == skill_key,
            ))
            evidence_count = len(skill.observations)
            new_proficiency = skill.score / 20
            if profile is None:
                db.add(CandidateSkillProfile(
                    user_id=user_id,
                    skill_key=skill_key,
                    skill_name=skill.name,
                    proficiency=new_proficiency,
                    confidence=skill.confidence,
                    evidence_count=evidence_count,
                    last_assessed_at=datetime.now(timezone.utc),
                    assessment_status="assessed",
                ))
            else:
                # Remove this session's prior contribution before adding its latest result.
                old_count = max(profile.evidence_count, 0)
                profile.proficiency = (
                    ((profile.proficiency or 0) * old_count + new_proficiency * evidence_count)
                    / max(old_count + evidence_count, 1)
                )
                profile.confidence = max(profile.confidence or 0, skill.confidence)
                profile.evidence_count = old_count + evidence_count
                profile.skill_name = skill.name
                profile.last_assessed_at = datetime.now(timezone.utc)
                profile.assessment_status = "assessed"
    return evaluation
