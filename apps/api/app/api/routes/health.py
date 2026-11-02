"""Health check endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app import __version__
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
@router.get("/healthz", response_model=HealthResponse, include_in_schema=False)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="interview-shala-api",
        version=__version__,
        timestamp=datetime.now(timezone.utc),
    )
