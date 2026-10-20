"""Shared FastAPI dependency providers.

Implements singleton-pattern dependency injection for heavyweight resources
(RecommenderService, CandidateRetriever) that should be created once at
startup and reused across all requests.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException

from src.services.recommender import RecommenderService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton container
# ---------------------------------------------------------------------------

_recommender_service: Optional[RecommenderService] = None


def get_recommender_service() -> RecommenderService:
    """FastAPI dependency that returns the shared RecommenderService singleton.

    Raises:
        HTTPException 503: If the service failed to initialize at startup.
    """
    if _recommender_service is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendation service is not yet initialized. Please retry in a moment.",
        )
    return _recommender_service


def init_recommender_service() -> RecommenderService:
    """Instantiate and cache the RecommenderService singleton.

    Called once during FastAPI lifespan startup. Safe to call multiple times —
    only the first call creates the instance.

    Returns:
        RecommenderService: The initialized singleton.

    Raises:
        Exception: Propagates any error from dataset loading or engine setup.
    """
    global _recommender_service
    if _recommender_service is None:
        logger.info("Initializing RecommenderService singleton...")
        _recommender_service = RecommenderService()
        _recommender_service.warm_up()
        logger.info("RecommenderService singleton ready.")
    return _recommender_service


def reset_recommender_service() -> None:
    """Clear the singleton (used in tests to force re-initialization)."""
    global _recommender_service
    _recommender_service = None
