"""HalluGuard FastAPI Application Entry Point.

Loads the LettuceDetect model once on application startup using FastAPI lifespan.
Provides REST API endpoints for hallucination verification, document extraction,
and context retrieval.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.verification import router as verification_router
from app.api.documents import router as documents_router
from app.config import settings
from app.services.detector_service import detector_service
from app.services.hybrid_detector_service import hybrid_detector_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("halluguard")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager: runs once on startup and once on shutdown."""
    logger.info("Initializing %s v%s...", settings.app_name, settings.app_version)

    # Load Hybrid models (LettuceDetect + DeBERTa-v3 NLI) once into memory
    try:
        logger.info("Loading Hybrid verification models on CPU...")
        hybrid_detector_service.load_models()
        logger.info("Hybrid verification pipeline ready for inference.")
    except Exception as e:
        logger.error(
            "FATAL: Failed to load hybrid models during startup: %s",
            e,
            exc_info=True,
        )
        # We don't crash app so /health can report degraded status if needed,
        # but hybrid_detector_service.is_loaded remains False.

    yield

    logger.info("Shutting down %s...", settings.app_name)


# FastAPI Application instance
app = FastAPI(
    title="HalluGuard API",
    description=(
        "Hallucination Detection Framework for Generative AI & RAG Applications. "
        "Powered by a production Hybrid Pipeline combining KRLabsOrg LettuceDetect ModernBERT "
        "token classifier and DeBERTa-v3 NLI semantic contradiction verifier."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(verification_router)
app.include_router(documents_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root endpoint redirecting info to documentation."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )

