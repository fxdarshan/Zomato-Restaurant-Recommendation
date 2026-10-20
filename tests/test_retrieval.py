"""Unit and integration tests for Phase 3 Candidate Retrieval and Relaxation Engine."""

import time
from pathlib import Path
import pytest

from src.config import settings
from src.retrieval.filter_engine import (
    CandidateRestaurant,
    CandidateRetriever,
    RetrievalQuery,
)
from src.retrieval.relaxation import (
    AdaptiveRelaxationEngine,
    RelaxationMetadata,
)


@pytest.fixture(scope="module")
def retriever() -> CandidateRetriever:
    """Fixture providing an initialized CandidateRetriever."""
    return CandidateRetriever()


@pytest.fixture(scope="module")
def relaxation_engine(retriever: CandidateRetriever) -> AdaptiveRelaxationEngine:
    """Fixture providing an AdaptiveRelaxationEngine instance."""
    return AdaptiveRelaxationEngine(retriever=retriever)


# ============================================================================
# 1. CandidateRetriever Initialization & Properties
# ============================================================================

def test_retriever_initialization(retriever: CandidateRetriever):
    """Verify that CandidateRetriever loads dataset and initializes indexes."""
    assert retriever.total_records > 10000
    assert len(retriever.unique_locations) >= 50
    assert len(retriever.unique_cuisines) >= 50
    assert "Indiranagar" in retriever.unique_locations
    assert "Koramangala" in retriever.unique_locations or any("koramangala" in loc.lower() for loc in retriever.unique_locations)
    assert "italian" in retriever.unique_cuisines
    assert "north indian" in retriever.unique_cuisines


# ============================================================================
# 2. Location Filtering & Resolution
# ============================================================================

def test_exact_location_filtering(retriever: CandidateRetriever):
    """Verify exact locality filtering isolates matching venues."""
    query = RetrievalQuery(location="Indiranagar", limit=10)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    for cand in candidates:
        assert (
            "indiranagar" in cand.location.lower()
            or "indiranagar" in cand.address.lower()
        )


def test_fuzzy_and_normalized_location_resolution(retriever: CandidateRetriever):
    """Verify spelling variations and spaces resolve accurately."""
    resolved, is_city = retriever.resolve_location("Indira Nagar")
    assert resolved == "Indiranagar"
    assert is_city is False

    resolved, is_city = retriever.resolve_location("Koramangla")
    assert "Koramangala" in (resolved or "")
    assert is_city is False

    resolved, is_city = retriever.resolve_location("Whitefeild")
    assert resolved == "Whitefield"
    assert is_city is False

    resolved, is_city = retriever.resolve_location("Bangalore")
    assert is_city is True

    resolved, is_city = retriever.resolve_location("Bengaluru")
    assert is_city is True


# ============================================================================
# 3. Budget Tier & Cost Filtering
# ============================================================================

def test_budget_tier_low(retriever: CandidateRetriever):
    """Verify low budget tier filters approx_cost <= BUDGET_LOW_MAX (400)."""
    query = RetrievalQuery(location="Indiranagar", budget_tier="low", limit=10)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    for cand in candidates:
        assert cand.approx_cost <= settings.BUDGET_LOW_MAX
        assert cand.budget_tier == "low"


def test_budget_tier_medium(retriever: CandidateRetriever):
    """Verify medium budget tier filters 400 < approx_cost <= 1200."""
    query = RetrievalQuery(location="Indiranagar", budget_tier="medium", limit=10)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    for cand in candidates:
        assert settings.BUDGET_LOW_MAX < cand.approx_cost <= settings.BUDGET_MEDIUM_MAX
        assert cand.budget_tier == "medium"


def test_budget_tier_high(retriever: CandidateRetriever):
    """Verify high budget tier filters approx_cost > 1200."""
    query = RetrievalQuery(location="Indiranagar", budget_tier="high", limit=10)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    for cand in candidates:
        assert cand.approx_cost > settings.BUDGET_MEDIUM_MAX
        assert cand.budget_tier == "high"


def test_custom_cost_target_and_intervals(retriever: CandidateRetriever):
    """Verify custom target_cost (+-20%) interval calculation."""
    query = RetrievalQuery(location="Bangalore", target_cost=1000, cost_tolerance=0.20, limit=10)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    for cand in candidates:
        assert 800 <= cand.approx_cost <= 1200


# ============================================================================
# 4. Cuisine & Rating Filtering
# ============================================================================

def test_cuisine_intersection(retriever: CandidateRetriever):
    """Verify cuisine set-intersection matching."""
    query = RetrievalQuery(location="Indiranagar", cuisines=["Italian"], limit=10)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    for cand in candidates:
        assert "italian" in [c.lower() for c in cand.cuisines]


def test_min_rating_filtering(retriever: CandidateRetriever):
    """Verify min_rating floor filter."""
    query = RetrievalQuery(location="Bangalore", min_rating=4.2, limit=15)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    for cand in candidates:
        assert cand.rating >= 4.2
        assert cand.is_rated is True


# ============================================================================
# 5. Deterministic Ordering & Tie-Breaking (TC-EDGE-08 / TC-EDGE-02)
# ============================================================================

def test_deterministic_popularity_ranking(retriever: CandidateRetriever):
    """Verify candidates are sorted by popularity_score descending."""
    query = RetrievalQuery(location="Bangalore", limit=20)
    candidates = retriever.retrieve(query)

    assert len(candidates) == 20
    scores = [c.popularity_score for c in candidates]
    assert scores == sorted(scores, reverse=True)


# ============================================================================
# 6. Chain / Brand Deduplication (TC-EDGE-09)
# ============================================================================

def test_brand_deduplication(retriever: CandidateRetriever):
    """Verify max_per_brand prevents chain crowding (e.g. 15 Domino's outlets)."""
    query = RetrievalQuery(location="Bangalore", cuisines=["Pizza"], max_per_brand=1, limit=15)
    candidates = retriever.retrieve(query)

    assert len(candidates) > 0
    names = [c.name.lower().strip() for c in candidates]
    # Each restaurant name should be unique
    assert len(names) == len(set(names))


# ============================================================================
# 7. DuckDB SQL Parity Check
# ============================================================================

def test_duckdb_sql_parity(retriever: CandidateRetriever):
    """Verify retrieve_duckdb produces identical top candidates to Polars retrieval."""
    query = RetrievalQuery(location="Indiranagar", budget_tier="medium", cuisines=["Italian"], min_rating=4.0, limit=10)
    res_polars = retriever.retrieve(query)
    res_duckdb = retriever.retrieve_duckdb(query)

    assert len(res_polars) == len(res_duckdb)
    for p, d in zip(res_polars, res_duckdb):
        assert p.rest_id == d.rest_id
        assert p.name == d.name


# ============================================================================
# 8. Performance Benchmark (< 20ms Exit Criteria)
# ============================================================================

def test_retrieval_latency_under_20ms(retriever: CandidateRetriever):
    """Verify retrieval executes well within the 20ms performance budget."""
    query = RetrievalQuery(
        location="Indiranagar",
        budget_tier="medium",
        cuisines=["Italian", "Pizza"],
        min_rating=4.0,
        limit=15,
    )
    # Warm run
    retriever.retrieve(query)

    latencies: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        candidates = retriever.retrieve(query)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    median_latency = sorted(latencies)[len(latencies) // 2]
    assert len(candidates) > 0
    assert median_latency < 20.0, f"Retrieval latency {median_latency:.2f}ms exceeded 20ms limit"


# ============================================================================
# 9. Adaptive Relaxation Engine Tests
# ============================================================================

def test_relaxation_strict_sufficient(relaxation_engine: AdaptiveRelaxationEngine):
    """Verify relaxation is NOT applied when initial criteria yield >= min_candidates."""
    query = RetrievalQuery(
        location="Indiranagar",
        budget_tier="medium",
        cuisines=["Italian"],
        min_rating=4.0,
        limit=15,
    )
    candidates, meta = relaxation_engine.retrieve_with_relaxation(query, min_candidates=5)

    assert len(candidates) >= 5
    assert meta.is_relaxed is False
    assert meta.relaxation_level == 0
    assert len(meta.relaxed_fields) == 0


def test_relaxation_level_2_rating_decrement(relaxation_engine: AdaptiveRelaxationEngine):
    """Verify Level 2 rating relaxation triggers when rating floor is too strict."""
    # Strict rating 4.8 in Indiranagar Italian produces fewer than 5 candidates
    query = RetrievalQuery(
        location="Indiranagar",
        cuisines=["Italian"],
        min_rating=4.8,
        limit=15,
    )
    candidates, meta = relaxation_engine.retrieve_with_relaxation(query, min_candidates=5)

    assert len(candidates) >= 5
    assert meta.is_relaxed is True
    assert meta.relaxation_level in (1, 2)
    assert "rating" in meta.relaxed_fields
    assert meta.final_candidate_count >= 5


def test_relaxation_level_3_location_broadening(relaxation_engine: AdaptiveRelaxationEngine):
    """Verify Level 3 location broadening triggers when sub-locality has no matches."""
    # Whitefield French: 0 French in Whitefield, but 10+ in Bangalore
    query = RetrievalQuery(
        location="Whitefield",
        cuisines=["French"],
        min_rating=4.0,
        limit=15,
    )
    candidates, meta = relaxation_engine.retrieve_with_relaxation(query, min_candidates=5)

    assert len(candidates) >= 5
    assert meta.is_relaxed is True
    assert meta.relaxation_level == 3
    assert "location" in meta.relaxed_fields


def test_relaxation_completely_impossible_query(relaxation_engine: AdaptiveRelaxationEngine):
    """Verify extreme query handles 0 candidates gracefully without crashing."""
    query = RetrievalQuery(
        location="FictitiousTown12345",
        cuisines=["NonExistentMartianCuisine"],
        min_cost=10,
        max_cost=20,
        min_rating=4.9,
    )
    candidates, meta = relaxation_engine.retrieve_with_relaxation(query, min_candidates=5)

    # Should not crash, returns list (even if empty or relaxed)
    assert isinstance(candidates, list)
    assert meta.is_relaxed is True
    assert meta.explanation != ""
