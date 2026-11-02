"""Track and update weaknesses from evaluation signals."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Severity
from app.models.weakness import Weakness, WeaknessEvidence
from app.schemas.session import SkillScore


def severity_from_score(score: float, max_score: float = 100.0) -> Severity:
    ratio = score / max_score if max_score else 0.0
    if ratio < 0.4:
        return Severity.CRITICAL
    if ratio < 0.55:
        return Severity.NEEDS_IMPROVEMENT
    if ratio < 0.7:
        return Severity.MODERATE
    return Severity.MILD


def recommended_exercise_for(skill: str) -> str:
    return (
        f"Run a focused 20-minute voice drill on '{skill}': explain the concept, "
        f"then answer 3 follow-up questions out loud with concrete examples."
    )


async def upsert_weaknesses_from_scores(
    db: AsyncSession,
    *,
    project_id,
    session_id,
    skill_scores: list[SkillScore],
    improvements: list[str] | None = None,
) -> list[Weakness]:
    """Create or update weaknesses for low-scoring skills."""
    updated: list[Weakness] = []

    for score in skill_scores:
        if score.max_score <= 0:
            continue
        ratio = score.score / score.max_score
        if ratio >= 0.7:
            continue

        result = await db.execute(
            select(Weakness)
            .where(Weakness.project_id == project_id, Weakness.skill == score.skill)
            .options(selectinload(Weakness.evidence_items))
        )
        weakness = result.scalar_one_or_none()
        severity = severity_from_score(score.score, score.max_score)
        evidence_text = (
            f"Scored {score.score:.0f}/{score.max_score:.0f} on {score.skill} in practice session."
        )

        if weakness is None:
            weakness = Weakness(
                project_id=project_id,
                skill=score.skill,
                severity=severity,
                observation_count=1,
                summary=f"Needs improvement in {score.skill}.",
                recommended_exercise=recommended_exercise_for(score.skill),
                recent_progress=None,
            )
            db.add(weakness)
            await db.flush()
        else:
            weakness.observation_count += 1
            weakness.severity = severity
            weakness.summary = (
                f"Observed {weakness.observation_count} times; latest score "
                f"{score.score:.0f}/{score.max_score:.0f}."
            )
            # Treat higher scores as progress
            weakness.recent_progress = round(ratio * 100, 1)

        db.add(
            WeaknessEvidence(
                weakness_id=weakness.id,
                session_id=session_id,
                evidence=evidence_text,
            )
        )
        updated.append(weakness)

    if improvements:
        for note in improvements[:5]:
            skill = note.strip()[:255] or "General communication"
            result = await db.execute(
                select(Weakness).where(Weakness.project_id == project_id, Weakness.skill == skill)
            )
            weakness = result.scalar_one_or_none()
            if weakness is None:
                weakness = Weakness(
                    project_id=project_id,
                    skill=skill,
                    severity=Severity.MODERATE,
                    observation_count=1,
                    summary=note,
                    recommended_exercise=recommended_exercise_for(skill),
                )
                db.add(weakness)
                await db.flush()
            else:
                weakness.observation_count += 1
                weakness.summary = note
            db.add(
                WeaknessEvidence(
                    weakness_id=weakness.id,
                    session_id=session_id,
                    evidence=note,
                )
            )
            updated.append(weakness)

    await db.flush()
    return updated


async def list_project_weaknesses(db: AsyncSession, project_id) -> list[Weakness]:
    result = await db.execute(
        select(Weakness)
        .where(Weakness.project_id == project_id)
        .options(selectinload(Weakness.evidence_items))
        .order_by(Weakness.updated_at.desc())
    )
    return list(result.scalars().all())
