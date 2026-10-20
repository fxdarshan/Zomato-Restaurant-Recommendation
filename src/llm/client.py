"""Groq LLM client wrapper for restaurant recommendations.

Provides structured JSON output generation via the official `groq` Python SDK,
exponential retries, strict timeout guards, and zero-hallucination
post-generation validation.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Optional

import groq as groq_sdk
from pydantic import ValidationError

from src.config import settings
from src.retrieval.filter_engine import CandidateRestaurant
from src.llm.prompts import SYSTEM_INSTRUCTION, build_recommendation_prompt
from src.llm.schemas import (
    LLMRecommendationOutput,
    QuerySummary,
    RecommendationResponse,
    RestaurantRecommendationItem,
    UserPreferenceRequest,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class GroqError(Exception):
    """Base exception for Groq LLM operations."""


class GroqAPIKeyMissingError(GroqError):
    """Raised when GROQ_API_KEY is not configured."""


class GroqTimeoutError(GroqError):
    """Raised when LLM call exceeds the latency budget."""


class GroqAPIError(GroqError):
    """Raised when the Groq API encounters a remote / transient error."""


class GroqGroundingError(GroqError):
    """Raised when LLM output violates candidate grounding boundaries."""


# ---------------------------------------------------------------------------
# Backward-compatible aliases (used by recommender.py & services/__init__)
# ---------------------------------------------------------------------------
GeminiError = GroqError
GeminiAPIKeyMissingError = GroqAPIKeyMissingError
GeminiTimeoutError = GroqTimeoutError
GeminiAPIError = GroqAPIError
GeminiGroundingError = GroqGroundingError


# ---------------------------------------------------------------------------
# Main client class
# ---------------------------------------------------------------------------


class GroqRecommenderClient:
    """Wrapper around the official Groq Python SDK (`groq`).

    Calls `client.chat.completions.create()` with `response_format={"type":
    "json_object"}` to enforce structured JSON output, then validates the
    response against the LLMRecommendationOutput Pydantic schema and runs a
    grounding check to eliminate hallucinated restaurant names.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        client: Optional[Any] = None,
    ) -> None:
        """Initialize Groq recommendation client.

        Args:
            api_key: Groq API key. Defaults to settings.GROQ_API_KEY.
            model: Groq model identifier. Defaults to settings.GROQ_MODEL.
            timeout: Maximum timeout per request in seconds. Defaults to
                settings.LLM_TIMEOUT_SECONDS.
            max_retries: Number of retry attempts on transient network failures.
            client: Optional pre-built groq.Groq client (useful for unit tests).
        """
        self.api_key: str = (api_key if api_key is not None else settings.GROQ_API_KEY).strip()
        self.model: str = model or settings.GROQ_MODEL
        self.timeout: float = float(timeout or settings.LLM_TIMEOUT_SECONDS)
        self.max_retries: int = max(0, max_retries)

        if client is not None:
            self._client = client
            self.is_configured: bool = True
        elif self.api_key:
            self._client = groq_sdk.Groq(api_key=self.api_key)
            self.is_configured = True
        else:
            self._client = None
            self.is_configured = False
            logger.warning(
                "GROQ_API_KEY is not configured. LLM calls will fail or fallback."
            )

    def generate_recommendations(
        self,
        request: UserPreferenceRequest,
        candidates: list[CandidateRestaurant],
        is_relaxed: bool = False,
        relaxation_level: int = 0,
        relaxation_explanation: Optional[str] = None,
    ) -> RecommendationResponse:
        """Analyze candidates via Groq, rank them, and return grounded recommendations.

        Args:
            request: User preference request.
            candidates: Pre-filtered CandidateRestaurant list from retrieval engine.
            is_relaxed: Whether constraint relaxation was applied in retrieval.
            relaxation_level: Stage of relaxation applied (0-3).
            relaxation_explanation: User-facing relaxation note if applicable.

        Returns:
            RecommendationResponse: Validated response conforming to API contract.

        Raises:
            GroqAPIKeyMissingError: If API key is not configured.
            GroqTimeoutError: If request times out.
            GroqAPIError: If Groq API throws unrecoverable exception.
            GroqGroundingError: If all candidate names returned by LLM are hallucinated.
        """
        query_summary = QuerySummary(
            location=request.location,
            budget_tier=request.budget_tier,
            target_cost=request.target_cost,
            cuisines=request.cuisines,
            min_rating=request.min_rating,
            vibe=request.vibe_and_preferences,
            total_candidates_analyzed=len(candidates),
            is_relaxed=is_relaxed,
            relaxation_level=relaxation_level,
            relaxation_explanation=relaxation_explanation,
        )

        # Empty candidate handling
        if not candidates:
            return RecommendationResponse(
                status="no_results",
                query_summary=query_summary,
                recommendations=[],
                concierge_note=(
                    "We couldn't find any restaurants matching your specific constraints. "
                    "Try broadening your location or expanding cuisine choices."
                ),
            )

        if not self.is_configured or not self._client:
            raise GroqAPIKeyMissingError(
                "Cannot invoke Groq API: GROQ_API_KEY is not configured in environment."
            )

        prompt = build_recommendation_prompt(request, candidates)

        # Groq chat messages: system + user turn
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt},
        ]

        # Retry loop with exponential back-off
        last_exception: Optional[Exception] = None
        raw_text: Optional[str] = None

        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.perf_counter()
                logger.debug(
                    "Calling Groq model '%s' (attempt %d/%d, timeout=%.1fs)...",
                    self.model,
                    attempt + 1,
                    self.max_retries + 1,
                    self.timeout,
                )

                # Dynamic token ceiling: allocate only what is needed for the requested count
                dynamic_max_tokens = min(
                    settings.LLM_MAX_TOKENS,
                    max(180, request.max_recommendations * 85 + 50),
                )

                create_kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": dynamic_max_tokens,
                    "timeout": self.timeout,
                }
                # For reasoning models (e.g., openai/gpt-oss-120b), throttle reasoning effort to 'low'
                # to strictly limit token consumption against the 8K TPM rate limit
                if any(kw in self.model.lower() for kw in ("oss", "reason", "r1", "qwq")):
                    create_kwargs["reasoning_effort"] = "low"

                chat_completion = self._client.chat.completions.create(**create_kwargs)

                elapsed = time.perf_counter() - start_time
                usage = getattr(chat_completion, "usage", None)
                p_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
                c_tok = getattr(usage, "completion_tokens", 0) if usage else 0
                tot_tok = getattr(usage, "total_tokens", 0) if usage else (p_tok + c_tok)
                logger.info(
                    "Groq API call succeeded in %.2fs (model=%s | prompt=%d, completion=%d, total=%d tokens | 8K TPM usage: %.1f%%).",
                    elapsed,
                    self.model,
                    p_tok,
                    c_tok,
                    tot_tok,
                    (tot_tok / 8000.0) * 100.0,
                )

                choice = chat_completion.choices[0]
                raw_text = (choice.message.content or "").strip()
                if raw_text:
                    break

            except (groq_sdk.APITimeoutError, TimeoutError) as exc:
                logger.warning(
                    "Groq API call timed out after %.1fs (attempt %d): %s",
                    self.timeout, attempt + 1, exc,
                )
                last_exception = GroqTimeoutError(
                    f"Groq API request timed out after {self.timeout}s: {exc}"
                )
            except groq_sdk.RateLimitError as exc:
                logger.warning("Groq rate limit hit (attempt %d): %s", attempt + 1, exc)
                last_exception = GroqAPIError(f"Groq rate limit exceeded: {exc}")
            except groq_sdk.APIStatusError as exc:
                logger.warning(
                    "Groq API status error %s (attempt %d): %s",
                    exc.status_code, attempt + 1, exc.message,
                )
                last_exception = GroqAPIError(f"Groq API error [{exc.status_code}]: {exc.message}")
            except groq_sdk.APIConnectionError as exc:
                logger.warning("Groq connection error (attempt %d): %s", attempt + 1, exc)
                last_exception = GroqAPIError(f"Groq connection failed: {exc}")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Unexpected Groq error (attempt %d): %s", attempt + 1, exc)
                last_exception = GroqAPIError(f"Unexpected Groq error: {exc}")

            if attempt < self.max_retries:
                backoff_delay = 0.5 * (2 ** attempt)
                logger.info("Retrying Groq call in %.2fs...", backoff_delay)
                time.sleep(backoff_delay)

        if not raw_text:
            if isinstance(last_exception, GroqTimeoutError):
                raise last_exception
            raise last_exception or GroqAPIError(
                "Failed to obtain response text from Groq API."
            )

        # Parse & validate structured output
        llm_output = self._parse_llm_output(raw_text)

        # Post-generation Grounding & Zero-Hallucination Filter
        validated_recs = self._ground_and_verify_recommendations(
            llm_output, candidates, request.max_recommendations
        )

        if not validated_recs:
            raise GroqGroundingError(
                "All recommended restaurants from LLM output were unverified or hallucinated."
            )

        return RecommendationResponse(
            status="success",
            query_summary=query_summary,
            recommendations=validated_recs,
            concierge_note=llm_output.concierge_note.strip(),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_llm_output(raw_text: str) -> LLMRecommendationOutput:
        """Strip any markdown code fences and parse into LLMRecommendationOutput."""
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return LLMRecommendationOutput.model_validate_json(cleaned)
        except ValidationError as exc:
            logger.error(
                "Pydantic validation failed for Groq JSON output: %s\nRaw: %s", exc, cleaned
            )
            try:
                data = json.loads(cleaned)
                return LLMRecommendationOutput.model_validate(data)
            except Exception as json_exc:
                raise GroqAPIError(
                    f"Failed to parse Groq structured output as JSON: {json_exc}"
                ) from exc

    @staticmethod
    def _ground_and_verify_recommendations(
        llm_output: LLMRecommendationOutput,
        candidates: list[CandidateRestaurant],
        max_count: int,
    ) -> list[RestaurantRecommendationItem]:
        """Validate every LLM recommendation against the ground-truth candidate pool.

        Prevents hallucinated names, prices, or ratings by merging verified
        candidate attributes with the LLM's explanation and badge only.
        """
        id_map: dict[str, CandidateRestaurant] = {c.rest_id: c for c in candidates}
        name_map: dict[str, CandidateRestaurant] = {
            c.name.lower().strip(): c for c in candidates
        }

        validated: list[RestaurantRecommendationItem] = []
        seen_ids: set[str] = set()

        for item in llm_output.recommendations:
            # Primary verification: exact rest_id match
            matched: Optional[CandidateRestaurant] = id_map.get(item.rest_id)

            # Secondary fallback: exact name match (handles rest_id typos)
            if not matched:
                matched = name_map.get(item.name.lower().strip())

            if not matched:
                logger.warning(
                    "Dropped hallucinated restaurant '%s' (rest_id='%s') — not in candidate pool.",
                    item.name,
                    item.rest_id,
                )
                continue

            if matched.rest_id in seen_ids:
                continue

            seen_ids.add(matched.rest_id)
            rec_item = RestaurantRecommendationItem(
                rank=len(validated) + 1,
                rest_id=matched.rest_id,
                name=matched.name,
                location=matched.location,
                address=matched.address,
                cuisines=matched.cuisines,
                rating=matched.rating,
                votes=matched.votes,
                approx_cost_for_two=matched.approx_cost,
                budget_tier=matched.budget_tier,
                highlights=matched.highlights,
                ai_explanation=item.ai_explanation.strip(),
                match_badge=item.match_badge.strip(),
                url=matched.url,
                online_order=matched.online_order,
                book_table=matched.book_table,
            )
            validated.append(rec_item)

            if len(validated) >= max_count:
                break

        return validated


# ---------------------------------------------------------------------------
# Backward-compatible alias — lets recommender.py import GeminiRecommenderClient
# without any changes while we fully migrate the naming
# ---------------------------------------------------------------------------
GeminiRecommenderClient = GroqRecommenderClient
