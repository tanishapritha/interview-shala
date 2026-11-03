"""Evidence-grounded transcript evaluation using a configured OpenRouter model.

No score is produced when the provider is unavailable or the model output cannot
be tied back to exact candidate transcript segments.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.intelligence import (
    CandidateEvidence,
    CandidateSkillProfile,
    SessionTranscriptSegment,
)
from app.models.session import PracticeSession

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerifiedObservation:
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


class EvaluationUnavailable(RuntimeError):
    """Evaluation could not be completed reliably."""


def _validate_payload(raw: dict[str, Any], segments: list[SessionTranscriptSegment]) -> TranscriptEvaluation:
    candidate_segments = [s for s in segments if s.speaker == "candidate" and s.is_final]
    by_id = {str(s.id): s for s in candidate_segments}
    skills: list[VerifiedSkill] = []
    for item in raw.get("skills", []):
        name = str(item.get("name", "")).strip()[:120]
        if not name:
            continue
        observations: list[VerifiedObservation] = []
        for obs in item.get("observations", []):
            source = by_id.get(str(obs.get("segment_id", "")))
            quote = str(obs.get("quote", "")).strip()
            if source is None or not quote or quote not in source.text:
                continue
            polarity = obs.get("polarity")
            if polarity not in {"positive", "negative", "neutral"}:
                continue
            confidence = float(obs.get("confidence", 0))
            if not 0 <= confidence <= 1:
                continue
            observations.append(VerifiedObservation(
                skill=name,
                polarity=polarity,
                evidence_type=str(obs.get("evidence_type", "answer_quality"))[:64],
                quote=quote,
                explanation=str(obs.get("explanation", ""))[:1000],
                confidence=confidence,
            ))
        # A score is only reportable when at least one candidate quote verifies it.
        if observations:
            score = float(item.get("score", -1))
            confidence = float(item.get("confidence", 0))
            if 0 <= score <= 100 and 0 <= confidence <= 1:
                skills.append(VerifiedSkill(
                    name=name, score=score, confidence=confidence,
                    rationale=str(item.get("rationale", ""))[:1000],
                    observations=tuple(observations),
                ))
    if not skills:
        raise EvaluationUnavailable("No model observations could be verified against candidate speech.")
    score = sum(s.score * s.confidence for s in skills) / max(sum(s.confidence for s in skills), 0.001)
    strengths = tuple(dict.fromkeys(
        s.rationale for s in skills if s.score >= 70 and s.rationale
    ))[:5]
    improvements = tuple(dict.fromkeys(
        s.rationale for s in skills if s.score < 70 and s.rationale
    ))[:5]
    return TranscriptEvaluation(
        score=round(score, 1),
        strengths=strengths,
        improvements=improvements,
        next_action=str(raw.get("next_action", "Review the cited evidence and practise the weakest assessed skill."))[:500],
        skills=tuple(skills),
    )


async def evaluate_transcript(
    db: AsyncSession, session: PracticeSession, segments: list[SessionTranscriptSegment]
) -> TranscriptEvaluation:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise EvaluationUnavailable("OpenRouter is not configured.")
    if not any(s.speaker == "candidate" and s.is_final and s.text.strip() for s in segments):
        raise EvaluationUnavailable("No final candidate transcript is available.")
    transcript = [
        {"id": str(s.id), "speaker": s.speaker, "text": s.text}
        for s in segments if s.is_final
    ]
    prompt = {
        "role": "You are a rigorous interview assessor. Assess only what the candidate actually said. "
        "Do not infer unseen work, intent, correctness, or skills. Return JSON only. "
        "Every observation must cite an exact substring from one candidate segment using its segment_id. "
        "Do not cite interviewer text. If evidence is insufficient, omit that skill.",
        "task": "Evaluate the candidate's answer quality, technical correctness, reasoning, depth and communication. "
        "Scores are 0-100 and confidence 0-1. Separate positive and negative observations.",
        "transcript": transcript,
        "output_schema": {
            "skills": [{"name":"string","score":0,"confidence":0.0,"rationale":"string",
                "observations":[{"segment_id":"uuid","quote":"exact candidate substring",
                "polarity":"positive|negative|neutral","evidence_type":"string",
                "explanation":"string","confidence":0.0}]}],
            "next_action":"string"
        }
    }
    async with httpx.AsyncClient(timeout=45) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json"},
                json={"model": settings.openrouter_model, "temperature": 0.1,
                      "response_format": {"type": "json_object"},
                      "messages": [{"role":"system","content":prompt["role"]},
                                   {"role":"user","content":json.dumps({k:v for k,v in prompt.items() if k != "role"})}]},
            )
            response.raise_for_status()
            raw_content = response.json()["choices"][0]["message"]["content"]
            raw = json.loads(raw_content)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("Transcript evaluation provider failed: %s", exc)
            raise EvaluationUnavailable("The transcript evaluator is temporarily unavailable.") from exc
    evaluation = _validate_payload(raw, segments)
    for skill in evaluation.skills:
        skill_key = skill.name.lower().replace(" ", "-")[:160]
        for obs in skill.observations:
            source = next(s for s in segments if str(s.id) in {
                str(o.get("segment_id")) for o in raw.get("skills", [])
                for o in o.get("observations", [])
            } and obs.quote in s.text)
            db.add(CandidateEvidence(
                user_id=(await db.get(PracticeSession, session.id)).project.user_id,
                project_id=session.project_id, session_id=session.id,
                transcript_segment_id=source.id, evidence_type=obs.evidence_type,
                polarity=obs.polarity, content=obs.explanation or obs.quote,
                confidence=obs.confidence,
            ))
        existing = await db.scalar(select(CandidateSkillProfile).where(
            CandidateSkillProfile.user_id == session.project.user_id,
            CandidateSkillProfile.skill_key == skill_key,
        ))
        if existing is None:
            existing = CandidateSkillProfile(
                user_id=session.project.user_id, skill_key=skill_key,
                skill_name=skill.name, proficiency=skill.score / 20,
                confidence=skill.confidence, evidence_count=len(skill.observations),
                assessment_status="assessed",
            )
            db.add(existing)
        else:
            old_weight = max(existing.evidence_count, 0)
            new_weight = len(skill.observations)
            existing.proficiency = (
                ((existing.proficiency or 0) * old_weight + skill.score / 20 * new_weight)
                / max(old_weight + new_weight, 1)
            )
            existing.confidence = max(existing.confidence or 0, skill.confidence)
            existing.evidence_count += new_weight
            existing.assessment_status = "assessed"
    return evaluation
