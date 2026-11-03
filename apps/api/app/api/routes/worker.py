"""Private API for the trusted LiveKit worker."""

from __future__ import annotations

import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.intelligence import SessionTranscriptSegment
from app.models.project import InterviewProject
from app.models.enums import SessionStatus
from app.models.session import PracticeSession

router = APIRouter(prefix="/internal/worker", tags=["internal-worker"])


WorkerDbSession = Annotated[AsyncSession, Depends(get_db)]
WorkerSettings = Annotated[Settings, Depends(get_settings)]


async def require_worker_secret(
    x_worker_secret: Annotated[str | None, Header(alias="X-Worker-Secret")] = None,
    settings: WorkerSettings = None,
) -> None:
    expected = settings.worker_shared_secret
    if (
        not expected
        or not x_worker_secret
        or not secrets.compare_digest(x_worker_secret, expected)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Worker authentication failed",
        )


class WorkerTranscriptSegment(BaseModel):
    sequence_number: int = Field(ge=0)
    speaker: str
    text: str = Field(min_length=1, max_length=20_000)
    elapsed_ms: int | None = Field(default=None, ge=0)
    is_final: bool = True


@router.get("/sessions/{session_id}", dependencies=[Depends(require_worker_secret)])
async def get_worker_session(session_id: UUID, db: WorkerDbSession) -> dict:
    result = await db.execute(
        select(PracticeSession, InterviewProject)
        .join(InterviewProject, InterviewProject.id == PracticeSession.project_id)
        .where(PracticeSession.id == session_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Practice session not found")
    session, project = row
    if session.status in {SessionStatus.COMPLETED, SessionStatus.FAILED}:
        raise HTTPException(status_code=409, detail="Practice session is no longer active")
    next_sequence = await db.scalar(
        select(func.coalesce(func.max(SessionTranscriptSegment.sequence_number), -1) + 1)
        .where(SessionTranscriptSegment.session_id == session_id)
    )
    return {
        "session_id": str(session.id),
        "project_id": str(project.id),
        "company": project.company,
        "role": project.role,
        "job_description": project.job_description,
        "round_type": session.round_type,
        "status": session.status,
        "next_sequence": int(next_sequence or 0),
    }


@router.post(
    "/sessions/{session_id}/transcript-segments",
    dependencies=[Depends(require_worker_secret)],
)
async def persist_worker_transcript(
    session_id: UUID,
    segments: list[WorkerTranscriptSegment],
    db: WorkerDbSession,
) -> dict:
    if not segments:
        return {"accepted": 0}
    if len(segments) > 100:
        raise HTTPException(status_code=422, detail="A maximum of 100 segments may be sent at once")
    exists = await db.scalar(select(PracticeSession.id).where(PracticeSession.id == session_id))
    if exists is None:
        raise HTTPException(status_code=404, detail="Practice session not found")
    session_status = await db.scalar(
        select(PracticeSession.status).where(PracticeSession.id == session_id)
    )
    if session_status in {SessionStatus.COMPLETED, SessionStatus.FAILED}:
        raise HTTPException(status_code=409, detail="Practice session is no longer active")

    accepted = 0
    for segment in segments:
        if segment.speaker not in {"candidate", "interviewer"}:
            raise HTTPException(status_code=422, detail="Unsupported transcript speaker")
        statement = (
            pg_insert(SessionTranscriptSegment)
            .values(
                session_id=session_id,
                sequence_number=segment.sequence_number,
                speaker=segment.speaker,
                text=segment.text,
                elapsed_ms=segment.elapsed_ms,
                is_final=segment.is_final,
                source="livekit",
            )
            .on_conflict_do_nothing(constraint="uq_transcript_session_sequence")
            .returning(SessionTranscriptSegment.id)
        )
        inserted = (await db.execute(statement)).scalar_one_or_none()
        accepted += int(inserted is not None)
    return {"accepted": accepted, "submitted": len(segments)}
