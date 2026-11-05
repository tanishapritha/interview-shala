"""Practice session routes including LiveKit token."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession, RequireIdentity
from app.models.enums import SessionStatus
from app.models.project import InterviewProject
from app.models.session import PracticeSession, SessionEvent, SkillAssessment
from app.models.intelligence import SessionTranscriptSegment
from app.schemas.transcript import (
    TranscriptIngestResponse,
    TranscriptSegmentCreate,
    TranscriptSegmentResponse,
)
from app.schemas.session import (
    LiveKitTokenResponse,
    PracticeSessionComplete,
    PracticeSessionCreate,
    PracticeSessionResponse,
    SkillScore,
)
from app.services.evaluation import evaluate_session
from app.services.transcript_evaluator import EvaluationUnavailable, evaluate_transcript
from app.services.livekit_token import create_session_token
from app.services.ownership import get_owned_project, get_owned_session, ownership_filter
from app.services.readiness import recompute_project_metrics
from app.services.serializers import session_to_response
from app.services.weakness_tracker import upsert_weaknesses_from_scores

router = APIRouter()


@router.get("", response_model=list[PracticeSessionResponse])
async def list_sessions(
    db: DbSession,
    auth: RequireIdentity,
    project_id: UUID | None = None,
) -> list[PracticeSessionResponse]:
    stmt = (
        select(PracticeSession)
        .join(InterviewProject, PracticeSession.project_id == InterviewProject.id)
        .where(ownership_filter(auth))
        .options(selectinload(PracticeSession.skill_assessments))
        .order_by(PracticeSession.created_at.desc())
    )
    if project_id is not None:
        stmt = stmt.where(PracticeSession.project_id == project_id)
    result = await db.execute(stmt)
    return [session_to_response(s) for s in result.scalars().all()]


@router.post("", response_model=PracticeSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: PracticeSessionCreate,
    db: DbSession,
    auth: RequireIdentity,
) -> PracticeSessionResponse:
    await get_owned_project(db, auth, body.project_id)
    session = PracticeSession(
        project_id=body.project_id,
        round_id=body.round_id,
        round_type=body.round_type,
        status=SessionStatus.PENDING,
        livekit_room_name=None,
        # A brand-new session has no assessments yet. Initialize the collection
        # so response serialization never triggers an async lazy-load.
        skill_assessments=[],
    )
    db.add(session)
    await db.flush()
    db.add(
        SessionEvent(
            session_id=session.id,
            event_type="session.created",
            payload={"roundType": body.round_type},
        )
    )
    await db.flush()
    return session_to_response(session)


@router.get("/{session_id}", response_model=PracticeSessionResponse)
async def get_session(
    session_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> PracticeSessionResponse:
    session = await get_owned_session(db, auth, session_id)
    return session_to_response(session)


@router.post("/{session_id}/token", response_model=LiveKitTokenResponse)
async def issue_livekit_token(
    session_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> LiveKitTokenResponse:
    session = await get_owned_session(db, auth, session_id)
    identity = (
        f"user:{auth.user_id}"
        if auth.user_id
        else f"anon:{(auth.anonymous_session_id or 'unknown')[:16]}"
    )
    room_name = session.livekit_room_name or f"interview-shala-{session.id}"
    creds = create_session_token(
        session_id=session.id,
        identity=identity,
        room_name=room_name,
    )
    session.livekit_room_name = creds.room_name
    if session.status == SessionStatus.PENDING:
        session.status = SessionStatus.CONNECTING
    db.add(
        SessionEvent(
            session_id=session.id,
            event_type="livekit.token_issued",
            payload={"roomName": creds.room_name},
        )
    )
    await db.flush()
    return LiveKitTokenResponse(
        token=creds.token,
        room_name=creds.room_name,
        livekit_url=creds.livekit_url,
        session_id=creds.session_id,
    )


@router.post("/{session_id}/complete", response_model=PracticeSessionResponse)
async def complete_session(
    session_id: UUID,
    body: PracticeSessionComplete,
    db: DbSession,
    auth: RequireIdentity,
) -> PracticeSessionResponse:
    session = await get_owned_session(db, auth, session_id)
    if session.status == SessionStatus.COMPLETED:
        return session_to_response(session)

    evaluation = evaluate_session(round_type=session.round_type, payload=body)
    transcript_result = await db.execute(
        select(SessionTranscriptSegment)
        .where(SessionTranscriptSegment.session_id == session_id)
        .order_by(SessionTranscriptSegment.sequence_number.asc())
    )
    transcript_segments = list(transcript_result.scalars().all())
    project_result = await db.execute(
        select(InterviewProject).where(InterviewProject.id == session.project_id)
    )
    project = project_result.scalar_one()
    try:
        assessed = await evaluate_transcript(
            db,
            session_id=session.id,
            project_id=session.project_id,
            user_id=project.user_id,
            segments=transcript_segments,
        )
        evaluation.score = assessed.score
        evaluation.strengths = list(assessed.strengths)
        evaluation.improvements = list(assessed.improvements)
        evaluation.next_action = assessed.next_action
        evaluation.skill_scores = [
            SkillScore(skill=skill.name, score=skill.score, max_score=100.0)
            for skill in assessed.skills
        ]
        evaluation.source = "verified_transcript"
    except EvaluationUnavailable as exc:
        # Completing a session must not be blocked by provider outages or
        # insufficient transcript evidence. No score is fabricated.
        evaluation.next_action = (
            "Your session was saved without a score because transcript evaluation "
            f"was unavailable: {str(exc)}"
        )

    session.status = SessionStatus.COMPLETED
    session.completed_at = datetime.now(timezone.utc)
    session.duration_seconds = body.duration_seconds
    session.questions_completed = body.questions_completed
    session.score = evaluation.score
    session.strengths = evaluation.strengths
    session.improvements = evaluation.improvements
    session.next_action = evaluation.next_action

    # Replace skill assessments
    for existing in list(session.skill_assessments or []):
        await db.delete(existing)
    await db.flush()

    for skill in evaluation.skill_scores:
        db.add(
            SkillAssessment(
                session_id=session.id,
                project_id=session.project_id,
                skill=skill.skill,
                score=skill.score,
                max_score=skill.max_score,
            )
        )

    await upsert_weaknesses_from_scores(
        db,
        project_id=session.project_id,
        session_id=session.id,
        skill_scores=evaluation.skill_scores,
        improvements=evaluation.improvements,
    )

    project = await get_owned_project(db, auth, session.project_id, load_plan=True)
    await recompute_project_metrics(db, project)

    db.add(
        SessionEvent(
            session_id=session.id,
            event_type="session.completed",
            payload={"score": evaluation.score, "source": evaluation.source},
        )
    )
    await db.flush()

    # Reload with assessments
    session = await get_owned_session(db, auth, session_id)
    return session_to_response(session)



@router.post(
    "/{session_id}/transcript-segments",
    response_model=TranscriptIngestResponse,
    status_code=status.HTTP_200_OK,
)
async def ingest_transcript_segments(
    session_id: UUID,
    body: list[TranscriptSegmentCreate],
    db: DbSession,
    auth: RequireIdentity,
) -> TranscriptIngestResponse:
    """Persist client-supplied transcript segments idempotently.

    These records are explicitly marked as client supplied and must not be
    treated as trusted evidence or used for scoring until a verified worker
    ingestion path is implemented.
    """
    if not body:
        raise HTTPException(status_code=422, detail="At least one transcript segment is required")
    if len(body) > 100:
        raise HTTPException(status_code=422, detail="A maximum of 100 segments may be sent at once")

    await get_owned_session(db, auth, session_id)
    accepted = 0
    already_present = 0
    persisted: list[SessionTranscriptSegment] = []

    for item in body:
        values = {
            "session_id": session_id,
            "sequence_number": item.sequence_number,
            "speaker": item.speaker,
            "text": item.text,
            "elapsed_ms": item.elapsed_ms,
            "is_final": item.is_final,
            "source": "client",
        }
        statement = (
            pg_insert(SessionTranscriptSegment)
            .values(**values)
            .on_conflict_do_nothing(
                constraint="uq_transcript_session_sequence"
            )
            .returning(SessionTranscriptSegment.id)
        )
        inserted_id = (await db.execute(statement)).scalar_one_or_none()
        if inserted_id is not None:
            accepted += 1
            segment = await db.get(SessionTranscriptSegment, inserted_id)
            persisted.append(segment)
            continue

        existing_result = await db.execute(
            select(SessionTranscriptSegment).where(
                SessionTranscriptSegment.session_id == session_id,
                SessionTranscriptSegment.sequence_number == item.sequence_number,
            )
        )
        existing = existing_result.scalar_one()
        matches = all(
            getattr(existing, field) == value
            for field, value in values.items()
            if field not in {"session_id", "source"}
        )
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A transcript segment already exists at this sequence number "
                    "with different content"
                ),
            )
        already_present += 1
        persisted.append(existing)

    persisted.sort(key=lambda segment: segment.sequence_number)
    return TranscriptIngestResponse(
        accepted=accepted,
        already_present=already_present,
        segments=[TranscriptSegmentResponse.model_validate(item) for item in persisted],
    )


@router.get(
    "/{session_id}/transcript-segments",
    response_model=list[TranscriptSegmentResponse],
)
async def list_transcript_segments(
    session_id: UUID,
    db: DbSession,
    auth: RequireIdentity,
) -> list[TranscriptSegmentResponse]:
    """Return a session transcript in stable sequence order."""
    await get_owned_session(db, auth, session_id)
    result = await db.execute(
        select(SessionTranscriptSegment)
        .where(SessionTranscriptSegment.session_id == session_id)
        .order_by(SessionTranscriptSegment.sequence_number.asc())
    )
    return [
        TranscriptSegmentResponse.model_validate(segment)
        for segment in result.scalars().all()
    ]
