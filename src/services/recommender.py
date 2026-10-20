"""Master Recommender Service — end-to-end pipeline orchestrator.

Coordinates candidate retrieval, adaptive relaxation, Groq LLM reasoning,
caching, and deterministic heuristic fallback into a single unified service.

Pipeline:
    1. Build cache key → check QueryCache → return immediately on HIT.
    2. Build RetrievalQuery from UserPreferenceRequest.
    3. AdaptiveRelaxationEngine.retrieve_with_relaxation() → candidates + metadata.
    4. Build QuerySummary from request + relaxation metadata.
    5. Attempt Groq LLM (GroqRecommenderClient.generate_recommendations()).
       - On success → cache response → return with status="success".
       - On any LLM failure / timeout → fall through to step 6.
    6. HeuristicFallbackRanker.rank() → return with status="fallback".
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from src.config import settings
from src.llm.client import (
    GeminiAPIError,
    GeminiAPIKeyMissingError,
    GeminiGroundingError,
    GeminiRecommenderClient,
    GeminiTimeoutError,
)
from src.llm.schemas import (
    QuerySummary,
    RecommendationResponse,
    UserPreferenceRequest,
)
from src.retrieval.filter_engine import CandidateRetriever, RetrievalQuery
from src.retrieval.relaxation import AdaptiveRelaxationEngine
from src.services.cache import QueryCache
from src.services.fallback import HeuristicFallbackRanker

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: convert UserPreferenceRequest → RetrievalQuery
# ---------------------------------------------------------------------------


def _build_retrieval_query(request: UserPreferenceRequest) -> RetrievalQuery:
    """Map user preference fields to a normalized RetrievalQuery.

    Args:
        request: Validated UserPreferenceRequest from the API layer.

    Returns:
        RetrievalQuery ready for CandidateRetriever.
    """
    return RetrievalQuery(
        location=request.location,
        budget_tier=request.budget_tier,
        target_cost=request.target_cost,
        cuisines=request.cuisines,
        min_rating=request.min_rating,
        limit=settings.DEFAULT_CANDIDATE_POOL_SIZE,
    )


# ---------------------------------------------------------------------------
# Master Recommender Service
# ---------------------------------------------------------------------------


class RecommenderService:
    """End-to-end restaurant recommendation service pipeline.

    Coordinates all subsystems into a single `.recommend()` call:
    - Candidate retrieval with adaptive relaxation (Phase 3)
    - Groq LLM reasoning for ranked, explained recommendations (Phase 4)
    - In-memory query caching to avoid duplicate LLM calls (Phase 5.2)
    - Deterministic heuristic fallback when LLM is unavailable (Phase 5.1)

    Attributes:
        cache: QueryCache instance for result memoization.
        llm_client: GroqRecommenderClient (or Gemini-compatible wrapper).
        relaxation_engine: AdaptiveRelaxationEngine wired to CandidateRetriever.
        fallback_ranker: HeuristicFallbackRanker for deterministic fallback.
    """

    def __init__(
        self,
        retriever: Optional[CandidateRetriever] = None,
        llm_client: Optional[GeminiRecommenderClient] = None,
        cache: Optional[QueryCache] = None,
        fallback_ranker: Optional[HeuristicFallbackRanker] = None,
    ) -> None:
        """Initialize the RecommenderService with all sub-components.

        All arguments are optional — production defaults are instantiated
        automatically, enabling the service to be constructed with zero config.
        Dependency injection is fully supported for unit testing.

        Args:
            retriever: CandidateRetriever instance. Auto-created if None.
            llm_client: LLM client wrapper. Auto-created if None using settings.
            cache: QueryCache instance. Auto-created if None using settings.
            fallback_ranker: Heuristic fallback ranker. Auto-created if None.
        """
        # Candidate retrieval & relaxation
        _retriever = retriever or CandidateRetriever()
        self.relaxation_engine = AdaptiveRelaxationEngine(retriever=_retriever)

        # LLM client (Groq-compatible — uses GeminiRecommenderClient wrapper)
        self.llm_client: GeminiRecommenderClient = llm_client or GeminiRecommenderClient()

        # Cache
        self.cache: QueryCache = cache or QueryCache(
            ttl_seconds=settings.CACHE_TTL_SECONDS,
            enabled=settings.ENABLE_QUERY_CACHE,
        )

        # Fallback ranker
        self.fallback_ranker: HeuristicFallbackRanker = fallback_ranker or HeuristicFallbackRanker()

        logger.info(
            "RecommenderService initialized. cache=%s llm_configured=%s",
            self.cache,
            self.llm_client.is_configured,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(self, request: UserPreferenceRequest) -> RecommendationResponse:
        """Execute the full recommendation pipeline for a user request.

        Pipeline steps:
            1. Cache lookup → return immediately on HIT.
            2. Build RetrievalQuery and invoke AdaptiveRelaxationEngine.
            3. Attempt Groq LLM call → on success, cache and return.
            4. On LLM failure → invoke HeuristicFallbackRanker, do NOT cache.

        Args:
            request: Validated UserPreferenceRequest from the API layer.

        Returns:
            RecommendationResponse with status in {"success", "fallback", "no_results"}.
        """
        pipeline_start = time.perf_counter()

        # ------------------------------------------------------------------
        # Step 1: Cache Lookup
        # ------------------------------------------------------------------
        cache_key = self.cache.make_key(request)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            elapsed = (time.perf_counter() - pipeline_start) * 1000
            logger.info(
                "Cache HIT for request (location='%s'). Returned in %.1fms.",
                request.location,
                elapsed,
            )
            return cached_response

        # ------------------------------------------------------------------
        # Step 2: Candidate Retrieval with Adaptive Relaxation
        # ------------------------------------------------------------------
        retrieval_query = _build_retrieval_query(request)

        retrieval_start = time.perf_counter()
        candidates, relaxation_meta = self.relaxation_engine.retrieve_with_relaxation(retrieval_query)
        retrieval_elapsed = (time.perf_counter() - retrieval_start) * 1000

        logger.info(
            "Retrieval complete: %d candidates in %.1fms (relaxed=%s, level=%d).",
            len(candidates),
            retrieval_elapsed,
            relaxation_meta.is_relaxed,
            relaxation_meta.relaxation_level,
        )

        # Build shared QuerySummary for both success and fallback paths
        query_summary = QuerySummary(
            location=request.location,
            budget_tier=request.budget_tier,
            target_cost=request.target_cost,
            cuisines=request.cuisines,
            min_rating=request.min_rating,
            vibe=request.vibe_and_preferences,
            total_candidates_analyzed=len(candidates),
            is_relaxed=relaxation_meta.is_relaxed,
            relaxation_level=relaxation_meta.relaxation_level,
            relaxation_explanation=relaxation_meta.explanation or None,
        )

        # Handle empty candidate pool before calling LLM
        if not candidates:
            logger.warning(
                "No candidates found for request (location='%s'). Returning no_results.",
                request.location,
            )
            return RecommendationResponse(
                status="no_results",
                query_summary=query_summary,
                recommendations=[],
                concierge_note=(
                    "We couldn't find any restaurants matching your specific constraints. "
                    "Try broadening your location or expanding your cuisine choices."
                ),
            )

        # ------------------------------------------------------------------
        # Step 3: LLM Reasoning (Groq via GeminiRecommenderClient wrapper)
        # ------------------------------------------------------------------
        llm_response: Optional[RecommendationResponse] = None
        llm_error: Optional[Exception] = None

        if self.llm_client.is_configured:
            llm_start = time.perf_counter()
            # Token budget optimization: pass only top candidates (4-6 max) to protect 8K TPM rate limit
            pool_cap = min(len(candidates), max(4, request.max_recommendations + 1))
            llm_candidates = candidates[:pool_cap]
            try:
                llm_response = self.llm_client.generate_recommendations(
                    request=request,
                    candidates=llm_candidates,
                    is_relaxed=relaxation_meta.is_relaxed,
                    relaxation_level=relaxation_meta.relaxation_level,
                    relaxation_explanation=relaxation_meta.explanation or None,
                )
                llm_elapsed = (time.perf_counter() - llm_start) * 1000
                logger.info("LLM call succeeded in %.1fms.", llm_elapsed)
            except GeminiAPIKeyMissingError as exc:
                llm_error = exc
                logger.warning("LLM API key missing — activating fallback: %s", exc)
            except GeminiTimeoutError as exc:
                llm_error = exc
                logger.warning("LLM call timed out — activating fallback: %s", exc)
            except GeminiGroundingError as exc:
                llm_error = exc
                logger.warning("LLM grounding check failed — activating fallback: %s", exc)
            except GeminiAPIError as exc:
                llm_error = exc
                logger.warning("LLM API error — activating fallback: %s", exc)
            except Exception as exc:  # noqa: BLE001
                llm_error = exc
                logger.exception("Unexpected LLM error — activating fallback: %s", exc)
        else:
            logger.info("LLM client not configured — using heuristic fallback directly.")

        # ------------------------------------------------------------------
        # Step 4a: LLM Success — Cache and Return
        # ------------------------------------------------------------------
        if llm_response is not None:
            self.cache.set(cache_key, llm_response)
            total_elapsed = (time.perf_counter() - pipeline_start) * 1000
            logger.info(
                "Pipeline complete (LLM path) for location='%s' in %.1fms. "
                "Recommendations: %d.",
                request.location,
                total_elapsed,
                len(llm_response.recommendations),
            )
            return llm_response

        # ------------------------------------------------------------------
        # Step 4b: LLM Failure — Heuristic Fallback (NOT cached)
        # ------------------------------------------------------------------
        fallback_response = self.fallback_ranker.rank(
            request=request,
            candidates=candidates,
            query_summary=query_summary,
            max_results=request.max_recommendations,
        )

        total_elapsed = (time.perf_counter() - pipeline_start) * 1000
        logger.info(
            "Pipeline complete (FALLBACK path) for location='%s' in %.1fms. "
            "Fallback recommendations: %d. LLM error: %s",
            request.location,
            total_elapsed,
            len(fallback_response.recommendations),
            type(llm_error).__name__ if llm_error else "N/A",
        )

        return fallback_response

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_cache_stats(self) -> dict:
        """Return current cache performance statistics."""
        return self.cache.stats

    def clear_cache(self) -> int:
        """Clear all cached responses. Returns number of entries cleared."""
        return self.cache.clear()

    def warm_up(self) -> None:
        """Pre-warm the retrieval engine (useful for API startup event).

        Logs dataset readiness stats without triggering an LLM call.
        """
        try:
            logger.info("RecommenderService warm-up: verifying retrieval engine is ready.")
            retriever = self.relaxation_engine.retriever
            logger.info(
                "Retrieval engine warm-up complete: %d total records loaded.",
                retriever._total_records,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Warm-up failed: %s", exc)
            raise
