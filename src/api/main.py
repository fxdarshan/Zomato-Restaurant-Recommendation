"""FastAPI application factory for the AI Restaurant Recommendation Service.

Phase 6 deliverable: production-ready REST API with:
- CORS middleware for cross-origin frontend access
- Lifespan context manager for startup warm-up and shutdown cleanup
- Centralized exception handlers (400, 422, 500)
- Structured request/response logging with duration metrics
- OpenAPI / Swagger docs at GET /docs
- ReDoc docs at GET /redoc
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

from src.api.dependencies import init_recommender_service, reset_recommender_service
from src.api.routes import router
from src.config import settings

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated on_event startup/shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: warm up on startup, clean up on shutdown."""
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Starting AI Restaurant Recommendation API v1.0.0")
    logger.info("Model  : %s", settings.GROQ_MODEL)
    logger.info("Dataset: %s", settings.PROCESSED_DATA_PATH)
    logger.info("Cache  : TTL=%ds enabled=%s", settings.CACHE_TTL_SECONDS, settings.ENABLE_QUERY_CACHE)
    logger.info("=" * 60)

    try:
        init_recommender_service()
        logger.info("Startup complete — API is ready to serve requests.")
    except FileNotFoundError as exc:
        logger.error(
            "STARTUP FAILED: Dataset not found. Run the ETL pipeline first.\n%s", exc
        )
        # Allow app to start in degraded mode so /health can report the issue
    except Exception as exc:
        logger.exception("STARTUP FAILED with unexpected error: %s", exc)

    yield  # ── Application runs here ──────────────────────────────────────

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down AI Restaurant Recommendation API...")
    reset_recommender_service()
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title="AI Restaurant Recommendation API",
        description=(
            "Zomato-style restaurant discovery powered by Groq LLM (qwen/qwen3.8-27b). "
            "Accepts user dining preferences and returns ranked, AI-explained recommendations "
            "with automatic heuristic fallback.\n\n"
            "**Data source**: Zomato Bangalore restaurant dataset via Hugging Face.\n"
            "**LLM**: Groq inference with zero-hallucination grounding validation."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS Middleware ───────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Request ID & Duration Logging Middleware ──────────────────────────
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())[:8]
        start = time.perf_counter()
        logger.debug(
            "→ %s %s [req_id=%s]", request.method, request.url.path, request_id
        )
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "← %s %s %d | %.1fms [req_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        response.headers["x-request-id"] = request_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)
        return response

    # ── Exception Handlers ────────────────────────────────────────────────

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        logger.warning("Pydantic validation error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("ValueError on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Bad Request", "detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred. Please try again.",
            },
        )

    # ── Root redirect ─────────────────────────────────────────────────────

    @app.get("/", include_in_schema=False)
    async def root():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {
            "service": "AI Restaurant Recommendation API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    # ── Register routes ───────────────────────────────────────────────────
    app.include_router(router)

    return app


# ---------------------------------------------------------------------------
# Application instance (imported by uvicorn)
# ---------------------------------------------------------------------------

app = create_app()


# ---------------------------------------------------------------------------
# Dev server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
