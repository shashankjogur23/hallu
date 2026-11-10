"""Health check API router."""

from fastapi import APIRouter
from app.config import settings
from app.schemas.verification import HealthResponse
from app.services.detector_service import detector_service
from app.services.nli_service import nli_service
from app.services.hybrid_detector_service import hybrid_detector_service
from app.services.supabase_service import supabase_service

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Get system health and model loading status",
    description="Returns backend health, detector model readiness, inference device, and database configuration status.",
)
async def get_health() -> HealthResponse:
    """Return system health and detector status."""
    is_healthy = detector_service.is_loaded
    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        detector_loaded=detector_service.is_loaded,
        nli_loaded=nli_service.is_loaded,
        hybrid_ready=hybrid_detector_service.is_loaded,
        model_name=hybrid_detector_service.model_name,
        device=detector_service.device,
        supabase_configured=supabase_service.is_configured,
        version=settings.app_version,
    )

