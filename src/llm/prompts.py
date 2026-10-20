"""Prompt templates, system directives, and candidate formatting for Groq LLM reasoning."""

from __future__ import annotations

import json
from typing import Any

from src.retrieval.filter_engine import CandidateRestaurant
from src.llm.schemas import UserPreferenceRequest

# High-density, token-minimized System Directive for Culinary AI Concierge
SYSTEM_INSTRUCTION = """You are the Zomato AI Culinary Concierge. Select top matching restaurants from the CANDIDATE list based on diner mood, cravings, and preferences.
RULES:
1. ONLY recommend from the CANDIDATE list using exact rest_id and name. Never hallucinate places, ratings, or prices.
2. For each pick: rank (1-based), rest_id, name, match_badge (e.g. 'Best Match', 'Romantic Patio', 'Top Value', 'Artisan Sourdough', 'Rooftop Vibe', 'Hidden Gem'), ai_explanation (strictly 1-2 engaging sentences, 25-40 words, clearly stating why AI matched the diner's request).
3. Return valid JSON: {"recommendations": [{"rank": 1, "rest_id": "...", "name": "...", "match_badge": "...", "ai_explanation": "..."}], "concierge_note": "1 warm, concise culinary concierge summary sentence"}"""

FEW_SHOT_EXAMPLES: list[dict[str, Any]] = []


def format_candidates_for_prompt(candidates: list[CandidateRestaurant], max_candidates: int = 5) -> str:
    """Format candidates into a token-minimal, dense JSON string without whitespace.

    Args:
        candidates: Pre-ranked candidate restaurants.
        max_candidates: Number of candidates to include (default 5 to preserve 8K TPM budget).

    Returns:
        str: Minified JSON string.
    """
    compact: list[dict[str, Any]] = []
    for c in candidates[:max_candidates]:
        item: dict[str, Any] = {
            "rest_id": c.rest_id,
            "name": c.name,
            "rating": round(c.rating, 1),
            "votes": c.votes,
            "cost": c.approx_cost,
            "cuisines": c.cuisines[:3],
        }
        if c.dish_liked_list:
            item["dishes"] = c.dish_liked_list[:2]
        elif c.highlights:
            item["features"] = c.highlights[:2]
        compact.append(item)

    return json.dumps(compact, ensure_ascii=False, separators=(",", ":"))


def build_recommendation_prompt(
    request: UserPreferenceRequest,
    candidates: list[CandidateRestaurant],
    max_candidates: int = 5,
) -> str:
    """Build compact user turn prompt.

    Args:
        request: Validated user preference request.
        candidates: Candidate restaurants.
        max_candidates: Maximum candidates to include in prompt.

    Returns:
        str: Token-minimized prompt.
    """
    needed = min(request.max_recommendations, len(candidates))
    candidates_json = format_candidates_for_prompt(candidates, max_candidates=max_candidates)
    vibe = (request.vibe_and_preferences or "Great food and ambiance").strip()[:140]

    prompt = (
        f"Location: {request.location} | Budget: {request.budget_tier or 'any'} | Min: {request.min_rating or 'any'}★ | Vibe: '{vibe}'\n"
        f"CANDIDATES: {candidates_json}\n"
        f"Pick top {needed} matching the vibe. Output JSON with 'recommendations' and 'concierge_note'."
    )
    return prompt

