"""Adaptive constraint relaxation engine for sparse restaurant search queries.

Implements multi-stage relaxation when initial criteria yield fewer than
the minimum candidate threshold (e.g. < 5 candidates):
1. Expand budget / cost boundaries (+-25%).
2. Decrement rating floor by 0.3 points (down to minimum 3.0).
3. Broaden location matching to city-wide and optionally relax cuisine constraints.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Any, Optional

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from pydantic import BaseModel, ConfigDict, Field

from src.config import settings
from src.retrieval.filter_engine import CandidateRestaurant, CandidateRetriever, RetrievalQuery

logger = logging.getLogger(__name__)


class RelaxationMetadata(BaseModel):
    """Metadata tracking adjustments made during adaptive query relaxation."""

    model_config = ConfigDict(extra="ignore")

    is_relaxed: bool = Field(
        default=False,
        description="True if any constraints were broadened beyond original user input",
    )
    relaxation_level: int = Field(
        default=0,
        description="Relaxation stage: 0=strict, 1=budget expanded, 2=rating lowered, 3=location/cuisines broadened",
    )
    relaxed_fields: list[str] = Field(
        default_factory=list,
        description="Names of constraint fields that were relaxed (e.g. ['budget', 'rating'])",
    )
    original_candidate_count: int = Field(
        default=0,
        description="Number of candidates returned under initial strict criteria",
    )
    final_candidate_count: int = Field(
        default=0,
        description="Number of candidates returned after relaxation was applied",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Detailed notes for each constraint alteration",
    )
    explanation: str = Field(
        default="",
        description="User-facing concise explanation of why and how filters were broadened",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert relaxation metadata to dictionary."""
        return self.model_dump()


class AdaptiveRelaxationEngine:
    """Orchestrates progressive constraint relaxation for candidate retrieval."""

    def __init__(
        self,
        retriever: Optional[CandidateRetriever] = None,
        min_candidates: int = settings.MIN_CANDIDATES_BEFORE_RELAXATION,
    ) -> None:
        """Initialize relaxation engine.

        Args:
            retriever: CandidateRetriever instance. If None, instantiates a default retriever.
            min_candidates: Minimum candidate count target before triggering relaxation (default 5).
        """
        self.retriever = retriever or CandidateRetriever()
        self.min_candidates = max(1, min_candidates)

    def retrieve_with_relaxation(
        self,
        query: RetrievalQuery,
        min_candidates: Optional[int] = None,
    ) -> tuple[list[CandidateRestaurant], RelaxationMetadata]:
        """Execute candidate retrieval with automatic progressive relaxation if results are sparse.

        Relaxation Funnel:
        - Level 0: Strict retrieval with exact user constraints.
        - Level 1: Expand budget / cost tolerance by +-25%.
        - Level 2: Decrement minimum rating floor by 0.3 (floor 3.0).
        - Level 3: Broaden location to city-wide and relax cuisine constraints.

        Args:
            query: User's initial search query.
            min_candidates: Target candidate count (defaults to self.min_candidates).

        Returns:
            tuple[list[CandidateRestaurant], RelaxationMetadata]:
                Final candidate list and transparency metadata explaining any adjustments.
        """
        target_count = min_candidates if min_candidates is not None else self.min_candidates

        # --------------------------------------------------------------------
        # Level 0: Strict Retrieval
        # --------------------------------------------------------------------
        initial_candidates = self.retriever.retrieve(query)
        initial_count = len(initial_candidates)

        if initial_count >= target_count:
            logger.debug("Strict retrieval satisfied with %d candidates (>= %d).", initial_count, target_count)
            return initial_candidates, RelaxationMetadata(
                is_relaxed=False,
                relaxation_level=0,
                relaxed_fields=[],
                original_candidate_count=initial_count,
                final_candidate_count=initial_count,
                notes=["Strict user constraints matched sufficient candidates."],
                explanation="Found matching restaurants with your exact preferences.",
            )

        logger.info(
            "Strict retrieval returned only %d candidates (< %d). Triggering adaptive relaxation...",
            initial_count,
            target_count,
        )

        relaxed_fields: list[str] = []
        notes: list[str] = []
        current_candidates = initial_candidates

        # Copy original query for modification
        relaxed_query = query.model_copy(deep=True)

        # --------------------------------------------------------------------
        # Level 1: Expand Cost / Budget Boundary by +-25%
        # --------------------------------------------------------------------
        budget_relaxed = False

        if relaxed_query.target_cost:
            relaxed_query.cost_tolerance = query.cost_tolerance + 0.25
            budget_relaxed = True
            notes.append(f"Expanded target cost tolerance to ±{int(relaxed_query.cost_tolerance * 100)}%.")
        elif relaxed_query.min_cost is not None or relaxed_query.max_cost is not None:
            if relaxed_query.min_cost is not None:
                relaxed_query.min_cost = max(50, int(round(relaxed_query.min_cost * 0.75)))
            if relaxed_query.max_cost is not None:
                relaxed_query.max_cost = int(round(relaxed_query.max_cost * 1.25))
            budget_relaxed = True
            notes.append(f"Expanded custom cost range to Rs.{relaxed_query.min_cost or 0} - Rs.{relaxed_query.max_cost or 'any'}.")
        elif relaxed_query.budget_tier:
            tier = relaxed_query.budget_tier.lower()
            if tier == "low":
                # Expand low budget upper limit by +25% (400 -> 500)
                relaxed_query.max_cost = int(round(settings.BUDGET_LOW_MAX * 1.25))
                relaxed_query.budget_tier = None
                budget_relaxed = True
                notes.append(f"Expanded low budget threshold up to Rs.{relaxed_query.max_cost}.")
            elif tier == "medium":
                # Expand medium budget (400*0.75=300, 1200*1.25=1500)
                relaxed_query.min_cost = int(round(settings.BUDGET_LOW_MAX * 0.75))
                relaxed_query.max_cost = int(round(settings.BUDGET_MEDIUM_MAX * 1.25))
                relaxed_query.budget_tier = None
                budget_relaxed = True
                notes.append(f"Expanded medium budget bracket to Rs.{relaxed_query.min_cost} - Rs.{relaxed_query.max_cost}.")
            elif tier == "high":
                # Expand high budget lower threshold (1200*0.75=900)
                relaxed_query.min_cost = int(round(settings.BUDGET_MEDIUM_MAX * 0.75))
                relaxed_query.budget_tier = None
                budget_relaxed = True
                notes.append(f"Expanded high budget bracket to include premium options from Rs.{relaxed_query.min_cost}.")

        if budget_relaxed:
            relaxed_fields.append("budget")
            candidates_lvl1 = self.retriever.retrieve(relaxed_query)
            if len(candidates_lvl1) > len(current_candidates):
                current_candidates = candidates_lvl1
                if len(current_candidates) >= target_count:
                    explanation = (
                        "We slightly expanded your budget boundaries (±25%) to discover additional top-rated options."
                    )
                    return current_candidates, RelaxationMetadata(
                        is_relaxed=True,
                        relaxation_level=1,
                        relaxed_fields=relaxed_fields,
                        original_candidate_count=initial_count,
                        final_candidate_count=len(current_candidates),
                        notes=notes,
                        explanation=explanation,
                    )

        # --------------------------------------------------------------------
        # Level 2: Decrement Rating Floor by 0.3 Points (Min 3.0 Floor)
        # --------------------------------------------------------------------
        if relaxed_query.min_rating is not None and relaxed_query.min_rating > 3.0:
            original_rating = relaxed_query.min_rating
            relaxed_query.min_rating = max(3.0, round(relaxed_query.min_rating - 0.3, 1))
            relaxed_fields.append("rating")
            notes.append(f"Lowered minimum rating threshold from {original_rating} stars to {relaxed_query.min_rating} stars.")

            candidates_lvl2 = self.retriever.retrieve(relaxed_query)
            if len(candidates_lvl2) > len(current_candidates):
                current_candidates = candidates_lvl2
                if len(current_candidates) >= target_count:
                    explanation = (
                        f"We adjusted the rating threshold slightly to {relaxed_query.min_rating} stars "
                        "and broadened pricing to present you with strong dining choices."
                    )
                    return current_candidates, RelaxationMetadata(
                        is_relaxed=True,
                        relaxation_level=2,
                        relaxed_fields=relaxed_fields,
                        original_candidate_count=initial_count,
                        final_candidate_count=len(current_candidates),
                        notes=notes,
                        explanation=explanation,
                    )

        # --------------------------------------------------------------------
        # Level 3: Broaden Location to City-Wide & Relax Cuisine Overlap
        # --------------------------------------------------------------------
        if relaxed_query.location and not relaxed_query.city_broadening:
            relaxed_query.city_broadening = True
            relaxed_fields.append("location")
            notes.append(
                f"Broadened location search from '{query.location}' to city-wide Bangalore metropolitan area."
            )

            candidates_lvl3 = self.retriever.retrieve(relaxed_query)
            if len(candidates_lvl3) > len(current_candidates):
                current_candidates = candidates_lvl3
                if len(current_candidates) >= target_count:
                    explanation = (
                        f"Few matches were available strictly within '{query.location}'. "
                        "We broadened the search across top nearby Bangalore dining hubs."
                    )
                    return current_candidates, RelaxationMetadata(
                        is_relaxed=True,
                        relaxation_level=3,
                        relaxed_fields=relaxed_fields,
                        original_candidate_count=initial_count,
                        final_candidate_count=len(current_candidates),
                        notes=notes,
                        explanation=explanation,
                    )

        # If still sparse and cuisines were constrained, relax cuisines
        if len(current_candidates) < target_count and relaxed_query.cuisines:
            relaxed_query.cuisines = None
            relaxed_fields.append("cuisines")
            notes.append("Relaxed specific cuisine filters to include popular local specialties.")

            candidates_lvl3_cuisines = self.retriever.retrieve(relaxed_query)
            if len(candidates_lvl3_cuisines) > len(current_candidates):
                current_candidates = candidates_lvl3_cuisines

        # Final assessment after all relaxation levels
        if len(current_candidates) > 0:
            explanation = (
                "To give you great recommendations, we expanded constraints on "
                + ", ".join(relaxed_fields)
                + " while maintaining high quality."
            )
            return current_candidates, RelaxationMetadata(
                is_relaxed=True,
                relaxation_level=3 if "location" in relaxed_fields or "cuisines" in relaxed_fields else 2,
                relaxed_fields=relaxed_fields,
                original_candidate_count=initial_count,
                final_candidate_count=len(current_candidates),
                notes=notes,
                explanation=explanation,
            )

        # Edge case: 0 candidates even after full relaxation
        logger.warning("Zero candidates found even after complete multi-tier relaxation.")
        return [], RelaxationMetadata(
            is_relaxed=True,
            relaxation_level=3,
            relaxed_fields=relaxed_fields or ["all"],
            original_candidate_count=initial_count,
            final_candidate_count=0,
            notes=notes + ["No matching venues found after full relaxation."],
            explanation=(
                "No restaurants matched these specific criteria even after full relaxation. "
                "Try searching for a broader location or clearing cuisine constraints."
            ),
        )
