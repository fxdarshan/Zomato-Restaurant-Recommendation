"""Deterministic heuristic fallback ranker for restaurant recommendations.

Used when the Groq LLM is unavailable, times out, or exhausts all retries.
Produces ranked recommendations purely from candidate popularity and rating scores
and generates template-based concierge explanations.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.retrieval.filter_engine import CandidateRestaurant
from src.llm.schemas import (
    QuerySummary,
    RecommendationResponse,
    RestaurantRecommendationItem,
    UserPreferenceRequest,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Badge assignment helpers
# ---------------------------------------------------------------------------

_BUDGET_BADGES: dict[str, str] = {
    "low": "Budget-Friendly Pick",
    "medium": "Best Value",
    "high": "Premium Experience",
}


def _assign_badge(candidate: CandidateRestaurant, request: UserPreferenceRequest, rank: int = 1) -> str:
    """Deterministically assign a match badge to a candidate restaurant."""
    if rank == 1:
        return "Crown Recommendation"
    if rank == 2:
        return "Alternative Enclave"
    if rank == 3:
        return "Social Enclave"

    vibe = (request.vibe_and_preferences or "").lower()
    if candidate.rating >= 4.5 and candidate.votes >= 200:
        return "Royal Gem"

    if any(kw in vibe for kw in ("date", "romantic", "anniversary", "candle")):
        return "Romantic Sanctuary"

    highlights_text = " ".join(h.lower() for h in candidate.highlights)
    if any(kw in highlights_text for kw in ("family", "kids", "spacious", "group")):
        return "Family Salon"

    if any(kw in highlights_text for kw in ("quick bite", "fast food", "takeaway", "pocket")):
        return "Bespoke Quick Bites"

    return _BUDGET_BADGES.get(candidate.budget_tier, "Curated Selection")


def _build_explanation(candidate: CandidateRestaurant) -> str:
    """Construct a template-based, factual explanation for the recommendation.

    Format:
    "Highly rated [Cuisine] option in [Location] with [Rating]★ based on [Votes]
    customer reviews. Known for [top dish/highlight]. Approx ₹[cost] for two."
    """
    cuisine_str = ", ".join(candidate.cuisines[:3]) if candidate.cuisines else "Multi-Cuisine"
    rating_str = f"{candidate.rating:.1f}★" if candidate.rating > 0 else "unrated"
    votes_str = f"{candidate.votes:,} customer reviews" if candidate.votes > 0 else "customer reviews"

    highlight_note = ""
    if candidate.highlights:
        top_highlight = candidate.highlights[0].strip()
        highlight_note = f" Known for {top_highlight}."

    explanation = (
        f"Highly rated {cuisine_str} option in {candidate.location} "
        f"with {rating_str} based on {votes_str}.{highlight_note} "
        f"Approx ₹{candidate.approx_cost:,} for two."
    )
    return explanation


# ---------------------------------------------------------------------------
# Main fallback ranker class
# ---------------------------------------------------------------------------


class HeuristicFallbackRanker:
    """Deterministic recommendation ranker that bypasses LLM inference.

    Ranks candidates by composite popularity score (rating * log10(votes + 1))
    and generates structured template explanations, ensuring the system always
    returns a useful response even when the LLM is unavailable.
    """

    def rank(
        self,
        request: UserPreferenceRequest,
        candidates: list[CandidateRestaurant],
        query_summary: QuerySummary,
        max_results: Optional[int] = None,
    ) -> RecommendationResponse:
        """Rank candidates deterministically and return a fallback response.

        Args:
            request: Original user preference request.
            candidates: Pre-filtered list of CandidateRestaurant objects.
            query_summary: Pre-built QuerySummary metadata for the response.
            max_results: Maximum recommendations to return. Defaults to request.max_recommendations.

        Returns:
            RecommendationResponse with status="fallback".
        """
        limit = max_results or request.max_recommendations

        if not candidates:
            logger.warning("HeuristicFallbackRanker: no candidates available; returning no_results.")
            return RecommendationResponse(
                status="no_results",
                query_summary=query_summary,
                recommendations=[],
                concierge_note=(
                    "We couldn't find any restaurants matching your specific constraints. "
                    "Try broadening your location or expanding your cuisine choices."
                ),
            )

        # Sort by composite_score descending (pre-computed: rating * log10(votes+1))
        ranked = sorted(candidates, key=lambda c: c.composite_score, reverse=True)
        top_candidates = ranked[:limit]

        recommendations: list[RestaurantRecommendationItem] = []
        for rank, candidate in enumerate(top_candidates, start=1):
            item = RestaurantRecommendationItem(
                rank=rank,
                rest_id=candidate.rest_id,
                name=candidate.name,
                location=candidate.location,
                address=candidate.address,
                cuisines=candidate.cuisines,
                rating=candidate.rating,
                votes=candidate.votes,
                approx_cost_for_two=candidate.approx_cost,
                budget_tier=candidate.budget_tier,
                highlights=candidate.highlights,
                ai_explanation=_build_explanation(candidate),
                match_badge=_assign_badge(candidate, request, rank=rank),
                url=candidate.url,
                online_order=candidate.online_order,
                book_table=candidate.book_table,
            )
            recommendations.append(item)

        # Build concierge note for fallback
        location_str = request.location.title()
        cuisine_str = (
            ", ".join(c.title() for c in (request.cuisines or [])[:2])
            or "your preferred cuisine"
        )
        concierge_note = (
            f"Here are the top-rated {cuisine_str} restaurants in {location_str}, "
            "ranked by popularity and customer reviews. "
            "Our AI concierge is temporarily unavailable — these picks are based on "
            "verified ratings and community feedback."
        )

        logger.info(
            "HeuristicFallbackRanker: returned %d fallback recommendations for location='%s'.",
            len(recommendations),
            request.location,
        )

        return RecommendationResponse(
            status="fallback",
            query_summary=query_summary,
            recommendations=recommendations,
            concierge_note=concierge_note,
        )
