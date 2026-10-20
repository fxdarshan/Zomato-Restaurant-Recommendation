"""API route handlers for the Restaurant Recommendation Service.

Endpoints:
    GET  /health                — Service health check & dataset status.
    GET  /api/v1/metadata       — Available locations, cuisines, budget tiers.
    POST /api/v1/recommend      — Main AI recommendation endpoint.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.api.dependencies import get_recommender_service
from src.config import settings
from src.llm.schemas import RecommendationResponse, UserPreferenceRequest
from src.services.recommender import RecommenderService

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(description="'healthy' or 'degraded'")
    service: str = Field(description="Service name")
    version: str = Field(description="API version")
    dataset_loaded: bool = Field(description="Whether the parquet dataset is loaded")
    total_records: int = Field(description="Total restaurant records in dataset")
    llm_configured: bool = Field(description="Whether the Groq API key is configured")
    groq_model: str = Field(description="Active Groq model identifier")
    cache_stats: dict = Field(description="Current cache performance statistics")


class MetadataResponse(BaseModel):
    """Metadata response for frontend dropdown population."""
    locations: list[str] = Field(description="All distinct locality names")
    cuisines: list[str] = Field(description="All distinct cuisine types")
    budget_tiers: list[dict[str, Any]] = Field(description="Budget tier definitions with price ranges")
    total_restaurants: int = Field(description="Total restaurants in dataset")


class ErrorResponse(BaseModel):
    """Standardized error response schema."""
    error: str
    detail: str
    request_id: str | None = None


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns service health, dataset availability, LLM configuration, and cache stats.",
    tags=["System"],
)
def health_check(
    svc: RecommenderService = Depends(get_recommender_service),
) -> HealthResponse:
    """Lightweight health check — does NOT hit the LLM or database."""
    retriever = svc.relaxation_engine.retriever
    return HealthResponse(
        status="healthy",
        service="AI Restaurant Recommendation API",
        version="1.0.0",
        dataset_loaded=True,
        total_records=retriever.total_records,
        llm_configured=svc.llm_client.is_configured,
        groq_model=settings.GROQ_MODEL,
        cache_stats=svc.get_cache_stats(),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/metadata
# ---------------------------------------------------------------------------


@router.get(
    "/api/v1/metadata",
    response_model=MetadataResponse,
    summary="Dataset Metadata",
    description=(
        "Returns all distinct locations, cuisines, and budget tier definitions "
        "for populating frontend filter dropdowns."
    ),
    tags=["Metadata"],
)
def get_metadata(
    svc: RecommenderService = Depends(get_recommender_service),
) -> MetadataResponse:
    """Return dropdown data for the frontend UI."""
    retriever = svc.relaxation_engine.retriever
    return MetadataResponse(
        locations=retriever.unique_locations,
        cuisines=retriever.unique_cuisines,
        budget_tiers=[
            {
                "value": "low",
                "label": "Budget Friendly",
                "description": f"Up to ₹{settings.BUDGET_LOW_MAX} for two",
                "max_cost": settings.BUDGET_LOW_MAX,
            },
            {
                "value": "medium",
                "label": "Mid Range",
                "description": f"₹{settings.BUDGET_LOW_MAX + 1}–₹{settings.BUDGET_MEDIUM_MAX} for two",
                "min_cost": settings.BUDGET_LOW_MAX + 1,
                "max_cost": settings.BUDGET_MEDIUM_MAX,
            },
            {
                "value": "high",
                "label": "Premium",
                "description": f"Above ₹{settings.BUDGET_MEDIUM_MAX} for two",
                "min_cost": settings.BUDGET_MEDIUM_MAX + 1,
            },
        ],
        total_restaurants=retriever.total_records,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/recommend
# ---------------------------------------------------------------------------


@router.post(
    "/api/v1/recommend",
    response_model=RecommendationResponse,
    summary="Get AI Restaurant Recommendations",
    description=(
        "Accepts user dining preferences and returns ranked, AI-explained restaurant "
        "recommendations. Uses Groq LLM for subjective vibe matching with automatic "
        "heuristic fallback if the LLM is unavailable."
    ),
    tags=["Recommendations"],
    responses={
        200: {"description": "Successful recommendation response (status: success | fallback | no_results)"},
        400: {"description": "Invalid request parameters", "model": ErrorResponse},
        422: {"description": "Request body validation error"},
        503: {"description": "Service not yet initialized"},
    },
)
def recommend(
    request_body: UserPreferenceRequest,
    request: Request,
    svc: RecommenderService = Depends(get_recommender_service),
) -> RecommendationResponse:
    """Main recommendation endpoint.

    Pipeline:
        1. Validate request (handled by Pydantic automatically).
        2. Check query cache → return immediately on HIT.
        3. Retrieve candidates via AdaptiveRelaxationEngine.
        4. Invoke Groq LLM for ranked, explained recommendations.
        5. On LLM failure → deterministic heuristic fallback.

    Args:
        request_body: Validated UserPreferenceRequest.
        request: FastAPI Request object (for logging request ID).
        svc: Injected RecommenderService singleton.

    Returns:
        RecommendationResponse with status in {"success", "fallback", "no_results"}.
    """
    start_time = time.perf_counter()
    request_id = request.headers.get("x-request-id", "")

    logger.info(
        "POST /api/v1/recommend | location='%s' budget='%s' cuisines=%s min_rating=%s vibe='%s' | req_id=%s",
        request_body.location,
        request_body.budget_tier,
        request_body.cuisines,
        request_body.min_rating,
        (request_body.vibe_and_preferences or "")[:60],
        request_id or "n/a",
    )

    try:
        response = svc.recommend(request_body)
    except ValueError as exc:
        logger.warning("Bad request for recommend endpoint: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in recommend endpoint: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="An unexpected internal error occurred. Please try again.",
        ) from exc

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
    logger.info(
        "POST /api/v1/recommend | status='%s' recommendations=%d elapsed=%.1fms | req_id=%s",
        response.status,
        len(response.recommendations),
        elapsed_ms,
        request_id or "n/a",
    )

    return response
