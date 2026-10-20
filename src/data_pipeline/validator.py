"""Automated validation module for processed restaurant data in Apache Parquet."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
from typing import Any

# Ensure project root is in sys.path for direct CLI script execution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


def validate_processed_dataset(parquet_path: Path | str = settings.PROCESSED_DATA_PATH) -> dict[str, Any]:
    """Validate that the processed Parquet file fulfills all data quality criteria.

    Verification & Exit Criteria:
    1. Parquet file exists and has rows > 0.
    2. No NaN / null values in 'rating', 'approx_cost', or 'location'.
    3. All 'approx_cost' values are positive integers (> 0).
    4. All 'cuisines' entries are valid non-empty lists of strings.
    5. All 'budget_tier' entries are one of {'low', 'medium', 'high'}.
    6. All 'rating' values are floats in range [0.0, 5.0].
    7. All 'rest_id' values are non-empty and strictly unique.

    Args:
        parquet_path: Path to the processed Parquet file.

    Returns:
        dict[str, Any]: Summary diagnostics of the validated dataset.

    Raises:
        FileNotFoundError: If the parquet file is not found.
        ValueError: If any validation checks fail.
    """
    file_path = Path(parquet_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {file_path}")

    df = pd.read_parquet(file_path, engine="pyarrow")
    total_records = len(df)
    if total_records == 0:
        raise ValueError("Processed dataset is empty (0 records).")

    errors: list[str] = []

    # 1. Required columns presence
    required_columns = [
        "rest_id",
        "name",
        "location",
        "rating",
        "is_rated",
        "votes",
        "approx_cost",
        "budget_tier",
        "cuisines",
    ]
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # 2. No NaN in rating, approx_cost, or location
    for col in ["rating", "approx_cost", "location"]:
        if col in df.columns:
            null_count = int(df[col].isna().sum())
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} NaN values (expected 0).")

    # 3. All approx_cost are numeric integers > 0
    if "approx_cost" in df.columns:
        invalid_costs = int((df["approx_cost"] <= 0).sum())
        if invalid_costs > 0:
            errors.append(f"Found {invalid_costs} non-positive costs in 'approx_cost'.")
        if not pd.api.types.is_integer_dtype(df["approx_cost"]):
            errors.append(f"'approx_cost' is not integer dtype (found {df['approx_cost'].dtype}).")

    # 4. All cuisines are valid non-empty lists/arrays of strings
    if "cuisines" in df.columns:
        empty_cuisines = 0
        for item in df["cuisines"]:
            if not isinstance(item, (list, tuple, np.ndarray)) or len(item) == 0:
                empty_cuisines += 1
            elif any(not str(c).strip() for c in item):
                empty_cuisines += 1
        if empty_cuisines > 0:
            errors.append(f"Found {empty_cuisines} records with empty or invalid 'cuisines' lists.")

    # 5. Budget tier validation
    if "budget_tier" in df.columns:
        valid_tiers = {"low", "medium", "high"}
        invalid_tiers = set(df["budget_tier"].unique()) - valid_tiers
        if invalid_tiers:
            errors.append(f"Found invalid budget tiers: {invalid_tiers}")

    # 6. Rating in range [0.0, 5.0]
    if "rating" in df.columns:
        out_of_range = int(((df["rating"] < 0.0) | (df["rating"] > 5.0)).sum())
        if out_of_range > 0:
            errors.append(f"Found {out_of_range} ratings outside [0.0, 5.0] range.")

    # 7. rest_id strictly unique
    if "rest_id" in df.columns:
        duplicates = int(df["rest_id"].duplicated().sum())
        if duplicates > 0:
            errors.append(f"Found {duplicates} duplicate 'rest_id' values.")

    if errors:
        error_msg = "Dataset validation failed with errors:\n" + "\n".join(f"- {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Compute summary statistics
    budget_distribution = df["budget_tier"].value_counts().to_dict()
    rated_count = int(df["is_rated"].sum()) if "is_rated" in df.columns else 0
    unique_locations = int(df["location"].nunique())

    summary: dict[str, Any] = {
        "status": "VALID",
        "total_records": total_records,
        "unique_locations": unique_locations,
        "rated_restaurants": rated_count,
        "unrated_restaurants": total_records - rated_count,
        "mean_rating_rated": round(float(df[df["is_rated"]]["rating"].mean()), 2) if rated_count > 0 else 0.0,
        "cost_min": int(df["approx_cost"].min()),
        "cost_median": int(df["approx_cost"].median()),
        "cost_max": int(df["approx_cost"].max()),
        "budget_distribution": budget_distribution,
        "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
    }

    logger.info("Validation successful: %s", summary)
    return summary


def main() -> None:
    """CLI entrypoint for dataset validator."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Validate processed Parquet dataset")
    parser.add_argument(
        "--path",
        type=str,
        default=str(settings.PROCESSED_DATA_PATH),
        help="Path to Parquet file to validate",
    )
    args = parser.parse_args()

    try:
        summary = validate_processed_dataset(args.path)
        print("=== Dataset Validation Passed ===")
        for k, v in summary.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"=== Dataset Validation FAILED ===\n{e}")
        exit(1)


if __name__ == "__main__":
    main()
