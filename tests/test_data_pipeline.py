"""Unit and integration tests for Phase 2 data pipeline (ETL)."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data_pipeline.preprocess import (
    assign_budget_tier,
    clean_cost_string,
    clean_cuisines,
    clean_location,
    clean_rating,
    compute_composite_score,
    compute_popularity_score,
    impute_missing_costs,
    preprocess_dataframe,
)
from src.data_pipeline.validator import validate_processed_dataset


# ============================================================================
# 1. Rating Normalization Tests (TC-EDGE-01)
# ============================================================================

def test_clean_rating_standard():
    """Verify standard ratings e.g. '4.1/5' parse correctly."""
    rating, is_rated = clean_rating("4.1/5")
    assert rating == 4.1
    assert is_rated is True

    rating, is_rated = clean_rating("4.0 /5")
    assert rating == 4.0
    assert is_rated is True

    rating, is_rated = clean_rating(" 3.8 /5 ")
    assert rating == 3.8
    assert is_rated is True


def test_clean_rating_edge_cases():
    """TC-EDGE-01: 'NEW', '-', NaN, and empty ratings -> 0.0 and is_rated=False."""
    rating, is_rated = clean_rating("NEW")
    assert rating == 0.0
    assert is_rated is False

    rating, is_rated = clean_rating("-")
    assert rating == 0.0
    assert is_rated is False

    rating, is_rated = clean_rating(np.nan)
    assert rating == 0.0
    assert is_rated is False

    rating, is_rated = clean_rating(None)
    assert rating == 0.0
    assert is_rated is False

    rating, is_rated = clean_rating("")
    assert rating == 0.0
    assert is_rated is False


# ============================================================================
# 2. Cost Normalization Tests (TC-EDGE-02)
# ============================================================================

def test_clean_cost_string_standard():
    """Verify standard cost strings parse to integers."""
    assert clean_cost_string("800") == 800
    assert clean_cost_string("1,200") == 1200
    assert clean_cost_string("₹ 1,500") == 1500
    assert clean_cost_string("Rs. 600") == 600


def test_clean_cost_string_ranges():
    """Verify range notations like '500-800' parse to midpoint integer."""
    assert clean_cost_string("500-800") == 650
    assert clean_cost_string("400 - 600") == 500


def test_clean_cost_string_missing_and_invalid():
    """TC-EDGE-02: Missing or unparseable cost strings return None for later imputation."""
    assert clean_cost_string(None) is None
    assert clean_cost_string(np.nan) is None
    assert clean_cost_string("") is None
    assert clean_cost_string("-") is None


# ============================================================================
# 3. Cuisine Tokenization Tests
# ============================================================================

def test_clean_cuisines_standard():
    """Verify comma-separated cuisines split to lowercase list."""
    cuisines = clean_cuisines("North Indian, Chinese, Fast Food")
    assert cuisines == ["north indian", "chinese", "fast food"]


def test_clean_cuisines_fallback_to_rest_type():
    """Verify missing cuisine falls back to rest_type."""
    cuisines = clean_cuisines(np.nan, rest_type="Cafe, Quick Bites")
    assert cuisines == ["cafe", "quick bites"]


def test_clean_cuisines_fallback_when_all_empty():
    """Verify missing cuisine and rest_type returns non-empty default."""
    cuisines = clean_cuisines(None, rest_type=None)
    assert cuisines == ["multi-cuisine"]
    assert len(cuisines) > 0


# ============================================================================
# 4. Location Cleaning Tests
# ============================================================================

def test_clean_location_resolution():
    """Verify location falls back to listed_in(city) or address."""
    assert clean_location("Indiranagar", "Koramangala", "123 Main St") == "Indiranagar"
    assert clean_location(np.nan, "Whitefield", "123 Main St") == "Whitefield"
    assert clean_location(None, None, "123, MG Road, Bangalore") == "MG Road"
    assert clean_location(None, None, None) == "Bangalore"


# ============================================================================
# 5. Budget Tier Assignment Tests
# ============================================================================

def test_assign_budget_tier():
    """Verify budget tier brackets (low: <= 400, medium: 401-1200, high: > 1200)."""
    assert assign_budget_tier(300) == "low"
    assert assign_budget_tier(400) == "low"
    assert assign_budget_tier(450) == "medium"
    assert assign_budget_tier(1200) == "medium"
    assert assign_budget_tier(1250) == "high"
    assert assign_budget_tier(2500) == "high"


# ============================================================================
# 6. Scoring Tests
# ============================================================================

def test_scoring_functions():
    """Verify popularity and composite scores are calculated deterministically."""
    pop_score = compute_popularity_score(4.5, 1000)
    assert pop_score > 0
    assert isinstance(pop_score, float)

    comp_score = compute_composite_score(4.5, 1000)
    assert 0.0 <= comp_score <= 5.0
    assert isinstance(comp_score, float)


# ============================================================================
# 7. Cost Imputation Tests
# ============================================================================

def test_impute_missing_costs_hierarchical():
    """Verify missing costs are imputed from locality/cuisine medians."""
    sample_df = pd.DataFrame([
        {"location": "Indiranagar", "primary_cuisine": "italian", "approx_cost": 1000},
        {"location": "Indiranagar", "primary_cuisine": "italian", "approx_cost": 1200},
        {"location": "Indiranagar", "primary_cuisine": "italian", "approx_cost": None},  # should be ~1100
        {"location": "Indiranagar", "primary_cuisine": "chinese", "approx_cost": 500},
        {"location": "Whitefield", "primary_cuisine": "burger", "approx_cost": None},  # fallback
    ])

    imputed = impute_missing_costs(sample_df)
    assert imputed["approx_cost"].isna().sum() == 0
    assert (imputed["approx_cost"] > 0).all()
    # Check row 2 got imputed to Indiranagar Italian median (1100)
    assert imputed.loc[2, "approx_cost"] == 1100


# ============================================================================
# 8. Preprocessing Pipeline & Deduplication Tests
# ============================================================================

def test_preprocess_dataframe_end_to_end():
    """Verify complete preprocessing pipeline on synthetic raw data."""
    raw_data = {
        "url": ["https://zomato.com/1", "https://zomato.com/2", "https://zomato.com/3"],
        "address": ["12 100ft Road, Indiranagar", "12 100ft Road, Indiranagar", "45 Koramangala"],
        "name": ["Pasta Palace", "Pasta Palace", "Curry Point"],
        "online_order": ["Yes", "Yes", "No"],
        "book_table": ["Yes", "No", "No"],
        "rate": ["4.3/5", "4.3/5", "NEW"],
        "votes": [1200, 300, 0],  # First Pasta Palace has more votes
        "location": ["Indiranagar", "Indiranagar", "Koramangala"],
        "rest_type": ["Casual Dining", "Casual Dining", "Quick Bites"],
        "dish_liked": ["Lasagna, Tiramisu", "Lasagna", None],
        "cuisines": ["Italian, Desserts", "Italian, Desserts", "North Indian"],
        "approx_cost(for two people)": ["1,100", "1,100", "350"],
        "listed_in(city)": ["Indiranagar", "Indiranagar", "Koramangala"],
    }
    raw_df = pd.DataFrame(raw_data)
    processed = preprocess_dataframe(raw_df)

    # Deduplication test: Pasta Palace duplicate dropped, keeping 1200 votes row
    assert len(processed) == 2
    assert "rest_id" in processed.columns
    assert processed["rest_id"].nunique() == 2

    # Verification criteria
    assert processed["rating"].isna().sum() == 0
    assert processed["approx_cost"].isna().sum() == 0
    assert processed["location"].isna().sum() == 0
    assert (processed["approx_cost"] > 0).all()

    # Budget tier
    pasta_row = processed[processed["name"] == "Pasta Palace"].iloc[0]
    assert pasta_row["budget_tier"] == "medium"
    assert pasta_row["votes"] == 1200
    assert "Online Ordering" in pasta_row["highlights"]
    assert "Table Booking" in pasta_row["highlights"]

    curry_row = processed[processed["name"] == "Curry Point"].iloc[0]
    assert curry_row["budget_tier"] == "low"
    assert curry_row["rating"] == 0.0
    assert curry_row["is_rated"] == False


# ============================================================================
# 9. Validator Tests
# ============================================================================

def test_validator_fails_on_corrupt_data(tmp_path: Path):
    """Verify validator catches and raises ValueError on invalid dataset."""
    bad_df = pd.DataFrame([
        {
            "rest_id": "rest_00001",
            "name": "Bad Venue",
            "location": "Indiranagar",
            "rating": 6.5,  # Invalid: > 5.0
            "is_rated": True,
            "votes": 10,
            "approx_cost": -100,  # Invalid: <= 0
            "budget_tier": "invalid_tier",  # Invalid
            "cuisines": [],  # Invalid: empty
        }
    ])
    bad_parquet = tmp_path / "bad.parquet"
    bad_df.to_parquet(bad_parquet, engine="pyarrow")

    with pytest.raises(ValueError, match="Dataset validation failed"):
        validate_processed_dataset(bad_parquet)


def test_validate_actual_processed_parquet():
    """Verify that the generated production Parquet file passes all validation checks."""
    from src.config import settings

    if settings.PROCESSED_DATA_PATH.exists():
        summary = validate_processed_dataset(settings.PROCESSED_DATA_PATH)
        assert summary["status"] == "VALID"
        assert summary["total_records"] > 10000
        assert summary["unique_locations"] > 50
        assert summary["cost_min"] > 0
        assert "low" in summary["budget_distribution"]
        assert "medium" in summary["budget_distribution"]
        assert "high" in summary["budget_distribution"]
