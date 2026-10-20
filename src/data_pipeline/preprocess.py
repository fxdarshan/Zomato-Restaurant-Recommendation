"""Data preprocessing, cleaning, normalization, and feature enrichment pipeline."""

from __future__ import annotations

import argparse
import logging
import math
from pathlib import Path
import re
import sys
from typing import Any, Optional

# Ensure project root is in sys.path for direct CLI script execution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


def clean_rating(raw_val: Any) -> tuple[float, bool]:
    """Normalize rating strings to numeric float and determine rated status.

    Handles values such as '4.1/5', '4.0 /5', 'NEW', '-', and missing values.

    Args:
        raw_val: Raw rating value from dataset.

    Returns:
        tuple[float, bool]: (rating_value, is_rated)
    """
    if pd.isna(raw_val) or raw_val is None:
        return 0.0, False

    val_str = str(raw_val).strip()
    if not val_str or val_str.upper() in ("NEW", "-", "OPENING SOON", "NAN", "NONE"):
        return 0.0, False

    # Match rating pattern e.g. "4.1/5", "4.0 /5", "3.8"
    match = re.search(r"([0-5](?:\.\d+)?)", val_str)
    if match:
        try:
            rating_num = float(match.group(1))
            if 0.0 <= rating_num <= 5.0:
                return round(rating_num, 1), True
        except ValueError:
            pass

    return 0.0, False


def clean_cost_string(raw_val: Any) -> int | None:
    """Parse raw cost string into an integer cost for two people.

    Handles ranges ('500-800'), commas ('1,200'), currency symbols ('₹800'), and nulls.

    Args:
        raw_val: Raw cost representation.

    Returns:
        int | None: Parsed positive integer cost, or None if unparseable/missing.
    """
    if pd.isna(raw_val) or raw_val is None:
        return None

    val_str = str(raw_val).strip()
    if not val_str or val_str.lower() in ("nan", "none", "-"):
        return None

    # Handle range notation like "500-800" or "500 - 800"
    range_match = re.search(r"(\d[\d,]*)\s*-\s*(\d[\d,]*)", val_str)
    if range_match:
        try:
            low = int(re.sub(r"[^\d]", "", range_match.group(1)))
            high = int(re.sub(r"[^\d]", "", range_match.group(2)))
            if low > 0 and high > 0:
                return int(round((low + high) / 2.0))
        except (ValueError, TypeError):
            pass

    # Strip currency symbols and non-digits
    digits_only = re.sub(r"[^\d]", "", val_str)
    if digits_only:
        try:
            parsed = int(digits_only)
            if parsed > 0:
                return parsed
        except ValueError:
            pass

    return None


def clean_cuisines(raw_val: Any, rest_type: str = "") -> list[str]:
    """Tokenize and normalize cuisine strings into a lowercase list.

    Ensures no empty list is returned by falling back to rest_type or default.

    Args:
        raw_val: Raw comma-separated cuisines string.
        rest_type: Optional restaurant type for fallback inference.

    Returns:
        list[str]: Normalized, non-empty list of lowercase cuisines.
    """
    cuisines: list[str] = []
    if pd.notna(raw_val) and raw_val:
        items = str(raw_val).split(",")
        cuisines = [item.strip().lower() for item in items if item.strip()]

    if not cuisines and pd.notna(rest_type) and rest_type:
        type_items = str(rest_type).split(",")
        cuisines = [t.strip().lower() for t in type_items if t.strip()]

    if not cuisines:
        cuisines = ["multi-cuisine"]

    return cuisines


def clean_location(location: Any, listed_in_city: Any, address: Any) -> str:
    """Normalize and impute missing restaurant location/locality.

    Args:
        location: Primary location column value.
        listed_in_city: Fallback city/neighborhood grouping column.
        address: Full street address.

    Returns:
        str: Valid non-empty location string.
    """
    if pd.notna(location) and str(location).strip() and str(location).lower() != "nan":
        return str(location).strip()

    if pd.notna(listed_in_city) and str(listed_in_city).strip() and str(listed_in_city).lower() != "nan":
        return str(listed_in_city).strip()

    if pd.notna(address) and str(address).strip():
        parts = [p.strip() for p in str(address).split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-2]

    return "Bangalore"


def assign_budget_tier(
    cost: int,
    low_max: int = settings.BUDGET_LOW_MAX,
    medium_max: int = settings.BUDGET_MEDIUM_MAX,
) -> str:
    """Classify cost into standardized budget tiers ('low', 'medium', 'high').

    Args:
        cost: Approx cost for two in INR.
        low_max: Upper boundary for low budget (inclusive).
        medium_max: Upper boundary for medium budget (inclusive).

    Returns:
        str: 'low', 'medium', or 'high'
    """
    if cost <= low_max:
        return "low"
    elif cost <= medium_max:
        return "medium"
    return "high"


def compute_popularity_score(rating: float, votes: int) -> float:
    """Compute popularity score: rating * log10(votes + 1).

    Args:
        rating: Restaurant star rating (0.0 to 5.0).
        votes: Review/vote count.

    Returns:
        float: Popularity score rounded to 4 decimals.
    """
    safe_votes = max(int(votes), 0)
    return round(float(rating) * math.log10(safe_votes + 1), 4)


def compute_composite_score(rating: float, votes: int) -> float:
    """Compute weighted composite score combining rating and vote log volume.

    Score = (Rating * 0.6) + (min(log10(votes + 1) / 5.0, 1.0) * 0.4)

    Args:
        rating: Restaurant star rating (0.0 to 5.0).
        votes: Review/vote count.

    Returns:
        float: Composite score rounded to 4 decimals.
    """
    safe_votes = max(int(votes), 0)
    vote_component = min(math.log10(safe_votes + 1) / 5.0, 1.0) * 0.4
    return round((float(rating) * 0.6) + vote_component, 4)


def extract_highlights(row: pd.Series) -> list[str]:
    """Extract descriptive badges and highlights from row attributes.

    Args:
        row: Pandas Series representing a restaurant record.

    Returns:
        list[str]: List of key highlight tags.
    """
    highlights: list[str] = []

    # Online order
    online_order = str(row.get("online_order", "")).strip().lower()
    if online_order in ("yes", "true", "1"):
        highlights.append("Online Ordering")

    # Table booking
    book_table = str(row.get("book_table", "")).strip().lower()
    if book_table in ("yes", "true", "1"):
        highlights.append("Table Booking")

    # High rating badge
    rating = float(row.get("rating", 0.0))
    if rating >= 4.5:
        highlights.append("Top Rated (4.5+ ★)")
    elif rating >= 4.2:
        highlights.append("Highly Rated (4.2+ ★)")

    # Popularity badge
    votes = int(row.get("votes", 0))
    if votes >= 1000:
        highlights.append("Local Favorite (1k+ Reviews)")

    # Top dishes from dish_liked
    dish_liked_raw = row.get("dish_liked")
    if pd.notna(dish_liked_raw) and dish_liked_raw:
        dishes = [d.strip() for d in str(dish_liked_raw).split(",") if d.strip()]
        if dishes:
            highlights.extend(dishes[:3])

    # Restaurant type
    rest_type_raw = row.get("rest_type")
    if pd.notna(rest_type_raw) and rest_type_raw:
        r_types = [t.strip() for t in str(rest_type_raw).split(",") if t.strip()]
        for rt in r_types[:2]:
            if rt not in highlights:
                highlights.append(rt)

    return highlights


def create_search_text(row: pd.Series) -> str:
    """Generate lowercased searchable text blob combining key attributes.

    Args:
        row: Pandas Series representing a restaurant record.

    Returns:
        str: Space-separated search token text.
    """
    name = str(row.get("name", "")).strip()
    location = str(row.get("location", "")).strip()
    address = str(row.get("address", "")).strip()
    cuisines_list = row.get("cuisines", [])
    cuisines_str = " ".join(cuisines_list) if isinstance(cuisines_list, (list, np.ndarray)) else str(cuisines_list)
    highlights_list = row.get("highlights", [])
    highlights_str = " ".join(highlights_list) if isinstance(highlights_list, (list, np.ndarray)) else str(highlights_list)
    rest_type = str(row.get("rest_type", "")).strip()

    search_tokens = [name, location, address, cuisines_str, highlights_str, rest_type]
    return " ".join([t.lower() for t in search_tokens if t])


def impute_missing_costs(df: pd.DataFrame, default_cost: int = 400) -> pd.DataFrame:
    """Perform hierarchical median imputation for missing or non-positive approx_cost.

    Hierarchy:
    1. Median of (location, primary_cuisine)
    2. Median of (location)
    3. Median of (primary_cuisine)
    4. Dataset-wide median

    Args:
        df: DataFrame with 'location', 'primary_cuisine', and 'approx_cost'.
        default_cost: Fallback cost if overall dataset has no valid costs.

    Returns:
        pd.DataFrame: DataFrame with all approx_cost values imputed and bounded.
    """
    valid_costs = df[df["approx_cost"].notna() & (df["approx_cost"] > 0)]

    if len(valid_costs) > 0:
        global_median = int(valid_costs["approx_cost"].median())
        loc_cuisine_med = (
            valid_costs.groupby(["location", "primary_cuisine"])["approx_cost"].median().round().astype(int)
        )
        loc_med = valid_costs.groupby("location")["approx_cost"].median().round().astype(int)
        cuisine_med = valid_costs.groupby("primary_cuisine")["approx_cost"].median().round().astype(int)
    else:
        global_median = default_cost
        loc_cuisine_med = pd.Series(dtype=int)
        loc_med = pd.Series(dtype=int)
        cuisine_med = pd.Series(dtype=int)

    def _resolve_cost(row: pd.Series) -> int:
        cost = row.get("approx_cost")
        if pd.notna(cost) and cost > 0:
            return int(cost)

        loc = row.get("location")
        cui = row.get("primary_cuisine")

        # 1. Location + Cuisine
        if (loc, cui) in loc_cuisine_med.index:
            return int(loc_cuisine_med[(loc, cui)])

        # 2. Location
        if loc in loc_med.index:
            return int(loc_med[loc])

        # 3. Cuisine
        if cui in cuisine_med.index:
            return int(cuisine_med[cui])

        # 4. Global
        return global_median

    df["approx_cost"] = df.apply(_resolve_cost, axis=1)
    # Clamp bounds: minimum Rs 50, maximum Rs 25000
    df["approx_cost"] = df["approx_cost"].clip(lower=50, upper=25000).astype(int)
    return df


def preprocess_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Execute complete end-to-end cleaning and feature engineering on raw dataset.

    Args:
        raw_df: Raw dataframe loaded from CSV or Hugging Face.

    Returns:
        pd.DataFrame: Cleaned, deduplicated, and feature-enriched DataFrame.
    """
    logger.info("Starting preprocessing on %d raw rows...", len(raw_df))
    df = raw_df.copy()

    # Standardize column names
    col_mapping = {
        "rate": "raw_rate",
        "approx_cost(for two people)": "raw_approx_cost",
    }
    df = df.rename(columns=col_mapping)

    # Ensure votes is integer
    df["votes"] = pd.to_numeric(df.get("votes", 0), errors="coerce").fillna(0).astype(int)

    # 1. Deduplication: sort by votes descending, keep most complete record
    subset_cols = ["name", "address", "location"]
    existing_subset = [c for c in subset_cols if c in df.columns]
    if existing_subset:
        initial_len = len(df)
        df = df.sort_values("votes", ascending=False).drop_duplicates(subset=existing_subset, keep="first")
        logger.info("Deduplication reduced rows from %d to %d.", initial_len, len(df))

    df = df.reset_index(drop=True)

    # 2. Location cleaning & imputation
    df["location"] = df.apply(
        lambda r: clean_location(r.get("location"), r.get("listed_in(city)"), r.get("address")),
        axis=1,
    )
    df["city"] = df.get("listed_in(city)", "Bangalore").fillna("Bangalore").astype(str)

    # 3. Rating normalization
    cleaned_ratings = df["raw_rate"].apply(clean_rating)
    df["rating"] = [r[0] for r in cleaned_ratings]
    df["is_rated"] = [r[1] for r in cleaned_ratings]

    # 4. Cuisine tokenization & normalization
    df["cuisines"] = df.apply(
        lambda r: clean_cuisines(r.get("cuisines"), str(r.get("rest_type", ""))),
        axis=1,
    )
    df["primary_cuisine"] = df["cuisines"].apply(lambda c: c[0] if c else "multi-cuisine")

    # 5. Cost normalization & hierarchical median imputation
    df["approx_cost"] = df["raw_approx_cost"].apply(clean_cost_string)
    df = impute_missing_costs(df)

    # 6. Budget tier classification
    df["budget_tier"] = df["approx_cost"].apply(assign_budget_tier)

    # 7. Popularity & composite scores
    df["popularity_score"] = df.apply(
        lambda r: compute_popularity_score(r["rating"], r["votes"]),
        axis=1,
    )
    df["composite_score"] = df.apply(
        lambda r: compute_composite_score(r["rating"], r["votes"]),
        axis=1,
    )

    # 8. Highlights & dish_liked list
    def _parse_dishes(raw_val: Any) -> list[str]:
        if pd.isna(raw_val) or not raw_val:
            return []
        return [d.strip() for d in str(raw_val).split(",") if d.strip()]

    df["dish_liked_list"] = df.get("dish_liked", pd.Series(dtype=object)).apply(_parse_dishes)
    df["highlights"] = df.apply(extract_highlights, axis=1)

    # 9. Search text field
    df["search_text"] = df.apply(create_search_text, axis=1)

    # 10. Assign unique identifier (rest_00001, rest_00002, ...)
    df["rest_id"] = [f"rest_{i+1:05d}" for i in range(len(df))]

    # Standardize string fields and fill remaining nulls
    for col in ["name", "address", "rest_type", "url"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # Select and order final canonical columns
    final_cols = [
        "rest_id",
        "name",
        "address",
        "location",
        "city",
        "rating",
        "is_rated",
        "votes",
        "approx_cost",
        "budget_tier",
        "cuisines",
        "primary_cuisine",
        "rest_type",
        "highlights",
        "dish_liked_list",
        "popularity_score",
        "composite_score",
        "search_text",
        "url",
        "online_order",
        "book_table",
    ]
    available_cols = [c for c in final_cols if c in df.columns]
    final_df = df[available_cols].copy()

    logger.info("Preprocessing complete. Final shape: %s", final_df.shape)
    return final_df


def run_pipeline(
    raw_path: Path | str = settings.RAW_DATA_PATH,
    output_path: Path | str = settings.PROCESSED_DATA_PATH,
) -> Path:
    """Run full ETL: load raw CSV, preprocess, and save to Parquet.

    Args:
        raw_path: Path to raw CSV file.
        output_path: Path to destination Parquet file.

    Returns:
        Path: Path to generated Parquet file.
    """
    raw_csv = Path(raw_path).resolve()
    dest_parquet = Path(output_path).resolve()

    if not raw_csv.exists():
        logger.info("Raw CSV not found at %s. Triggering download...", raw_csv)
        from src.data_pipeline.download_dataset import download_dataset

        download_dataset(output_path=raw_csv)

    logger.info("Loading raw dataset from %s...", raw_csv)
    raw_df = pd.read_csv(raw_csv, encoding="utf-8", low_memory=False)

    cleaned_df = preprocess_dataframe(raw_df)

    dest_parquet.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Writing cleaned dataset to Apache Parquet at %s...", dest_parquet)
    cleaned_df.to_parquet(dest_parquet, engine="pyarrow", index=False)

    file_size_mb = dest_parquet.stat().st_size / (1024 * 1024)
    logger.info(
        "Successfully wrote %d records to %s (%.2f MB).",
        len(cleaned_df),
        dest_parquet,
        file_size_mb,
    )

    return dest_parquet


def main() -> None:
    """CLI entrypoint for data preprocessing pipeline."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Preprocess and transform Zomato dataset into Parquet")
    parser.add_argument(
        "--raw-path",
        type=str,
        default=str(settings.RAW_DATA_PATH),
        help="Path to raw CSV dataset",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(settings.PROCESSED_DATA_PATH),
        help="Path to output Parquet file",
    )

    args = parser.parse_args()
    run_pipeline(raw_path=args.raw_path, output_path=args.output_path)


if __name__ == "__main__":
    main()
