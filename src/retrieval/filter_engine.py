"""High-performance candidate retrieval and filtering engine.

Backed by in-memory columnar processing (Polars & DuckDB) over zomato_cleaned.parquet
for sub-20ms candidate pruning and deterministic ranking.
"""

from __future__ import annotations

import difflib
import logging
from pathlib import Path
import re
import sys
from typing import Any, Optional

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from pydantic import BaseModel, ConfigDict, Field
import polars as pl

from src.config import settings

logger = logging.getLogger(__name__)


class RetrievalQuery(BaseModel):
    """Structured search query for candidate restaurant filtering."""

    model_config = ConfigDict(extra="ignore")

    location: Optional[str] = Field(
        default=None,
        description="Target locality, neighborhood, or city name (e.g. 'Indiranagar', 'Bangalore')",
    )
    budget_tier: Optional[str] = Field(
        default=None,
        description="Standardized budget category: 'low' (<=400), 'medium' (401-1200), 'high' (>1200)",
    )
    min_cost: Optional[int] = Field(
        default=None,
        description="Explicit lower cost bound for two people in INR",
    )
    max_cost: Optional[int] = Field(
        default=None,
        description="Explicit upper cost bound for two people in INR",
    )
    target_cost: Optional[int] = Field(
        default=None,
        description="Target price point around which cost tolerance interval is derived",
    )
    cost_tolerance: float = Field(
        default=0.20,
        description="Percentage tolerance applied when target_cost or budget range is expanded (default +-20%)",
    )
    cuisines: Optional[list[str]] = Field(
        default=None,
        description="List of desired cuisines (restaurant must serve at least one)",
    )
    min_rating: Optional[float] = Field(
        default=None,
        description="Minimum star rating filter (0.0 to 5.0)",
    )
    limit: int = Field(
        default=settings.DEFAULT_CANDIDATE_POOL_SIZE,
        description="Maximum number of candidates to retrieve (default: 15)",
    )
    city_broadening: bool = Field(
        default=False,
        description="If True, broadens search to city-wide (all Bangalore localities)",
    )
    max_per_brand: int = Field(
        default=1,
        description="Maximum outlets of the same restaurant brand allowed in the candidate pool",
    )


class CandidateRestaurant(BaseModel):
    """Normalized candidate restaurant representation."""

    model_config = ConfigDict(extra="ignore")

    rest_id: str
    name: str
    address: str
    location: str
    city: str
    rating: float
    is_rated: bool
    votes: int
    approx_cost: int
    budget_tier: str
    cuisines: list[str]
    primary_cuisine: str
    rest_type: str
    highlights: list[str] = Field(default_factory=list)
    dish_liked_list: list[str] = Field(default_factory=list)
    popularity_score: float
    composite_score: float
    url: str = ""
    online_order: str = ""
    book_table: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert candidate to standard serializable dictionary."""
        return self.model_dump()


def _normalize_brand_name(name: str) -> str:
    """Normalize restaurant name to identify chain brands for deduplication."""
    cleaned = name.lower().strip()
    cleaned = re.sub(r"['’\"`\-.]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Remove common location suffixes like 'indiranagar', 'koramangala', 'outlet', etc.
    cleaned = re.sub(r"\b(outlet|branch|express|kiosk|cloud kitchen)\b", "", cleaned).strip()
    return cleaned


class CandidateRetriever:
    """High-performance candidate retrieval engine backed by Polars & DuckDB."""

    def __init__(self, parquet_path: Path | str | None = None) -> None:
        """Initialize and warm up in-memory table.

        Args:
            parquet_path: Path to zomato_cleaned.parquet file. Defaults to settings.PROCESSED_DATA_PATH.
        """
        self.parquet_path = Path(parquet_path or settings.PROCESSED_DATA_PATH).resolve()
        if not self.parquet_path.exists():
            raise FileNotFoundError(
                f"Cleaned dataset not found at {self.parquet_path}. Run ETL pipeline first."
            )

        logger.info("Loading in-memory dataset from %s...", self.parquet_path)
        self._df: pl.DataFrame = pl.read_parquet(self.parquet_path)
        self._total_records: int = len(self._df)

        # Warm in-memory DuckDB connection with zero-copy Arrow registration
        import duckdb
        self._duckdb_con = duckdb.connect(":memory:")
        self._duckdb_con.register("restaurants", self._df.to_arrow())

        # Build canonical locality index for fuzzy and normalization lookup
        self._unique_locations: list[str] = self._df["location"].unique().to_list()
        self._loc_normalized_map: dict[str, str] = {
            self._simplify_str(loc): loc for loc in self._unique_locations
        }

        # Build set of all unique cuisines
        all_cuisines: set[str] = set()
        for cuisine_list in self._df["cuisines"].to_list():
            if isinstance(cuisine_list, (list, tuple)):
                all_cuisines.update(str(c).lower().strip() for c in cuisine_list if c)
        self._unique_cuisines: set[str] = all_cuisines

        logger.info(
            "CandidateRetriever ready: %d records, %d unique locations, %d unique cuisines.",
            self._total_records,
            len(self._unique_locations),
            len(self._unique_cuisines),
        )

    @staticmethod
    def _simplify_str(val: str) -> str:
        """Strip non-alphanumeric characters and lowercase for string normalization."""
        return re.sub(r"[^a-z0-9]", "", val.lower())

    def resolve_location(self, raw_location: str | None) -> tuple[str | None, bool]:
        """Resolve a user-provided location to a canonical locality or city-wide search.

        Args:
            raw_location: User input string (e.g. 'Indiranagar', 'Indira Nagar', 'Bangalore').

        Returns:
            tuple[canonical_location_or_none, is_city_wide]
        """
        if not raw_location or not str(raw_location).strip():
            return None, True

        query = str(raw_location).strip()
        simplified = self._simplify_str(query)

        # Detect metropolitan city-level requests (Bangalore / Bengaluru)
        if simplified in ("bangalore", "bengaluru", "bangaluru", "blr"):
            return "Bangalore", True

        # Exact simplified match
        if simplified in self._loc_normalized_map:
            return self._loc_normalized_map[simplified], False

        # Substring search in locations
        for simple_key, canonical in self._loc_normalized_map.items():
            if simple_key in simplified or simplified in simple_key:
                return canonical, False

        # Fuzzy matching using difflib
        matches = difflib.get_close_matches(query, self._unique_locations, n=1, cutoff=0.7)
        if matches:
            return matches[0], False

        # If location contains 'bangalore' along with a sub-locality e.g. "Indiranagar, Bangalore"
        parts = [p.strip() for p in re.split(r"[,/|-]", query) if p.strip()]
        for part in parts:
            part_simp = self._simplify_str(part)
            if part_simp in self._loc_normalized_map:
                return self._loc_normalized_map[part_simp], False
            part_matches = difflib.get_close_matches(part, self._unique_locations, n=1, cutoff=0.7)
            if part_matches:
                return part_matches[0], False

        # Fallback to substring query as-is without restricting to single locality
        return query, False

    def retrieve(self, query: RetrievalQuery) -> list[CandidateRestaurant]:
        """Filter and retrieve top candidate restaurants matching the query.

        Applies multi-condition pruning:
        - Location exact/fuzzy match or city-wide
        - Budget tier or cost interval
        - Cuisine set intersection
        - Rating threshold
        - Brand deduplication (limits max branches per brand)
        - Deterministic ranking: Popularity score DESC, approx_cost ASC, name ASC

        Args:
            query: RetrievalQuery object with search constraints.

        Returns:
            list[CandidateRestaurant]: Top candidates up to query.limit.
        """
        df = self._df
        filters: list[pl.Expr] = []

        # 1. Location Pruning
        if query.location and not query.city_broadening:
            resolved_loc, is_city_wide = self.resolve_location(query.location)
            if not is_city_wide and resolved_loc:
                # Match location or address
                escaped_loc = re.escape(resolved_loc.lower())
                filters.append(
                    (pl.col("location").str.to_lowercase() == resolved_loc.lower())
                    | (pl.col("address").str.to_lowercase().str.contains(escaped_loc))
                )

        # 2. Budget Pruning
        cost_min: Optional[int] = None
        cost_max: Optional[int] = None

        if query.target_cost and query.target_cost > 0:
            tol = query.cost_tolerance
            cost_min = int(round(query.target_cost * (1.0 - tol)))
            cost_max = int(round(query.target_cost * (1.0 + tol)))
        elif query.min_cost is not None or query.max_cost is not None:
            cost_min = query.min_cost
            cost_max = query.max_cost
        elif query.budget_tier:
            tier = query.budget_tier.lower().strip()
            if tier == "low":
                cost_max = settings.BUDGET_LOW_MAX
            elif tier == "medium":
                cost_min = settings.BUDGET_LOW_MAX + 1
                cost_max = settings.BUDGET_MEDIUM_MAX
            elif tier == "high":
                cost_min = settings.BUDGET_MEDIUM_MAX + 1

        if cost_min is not None:
            filters.append(pl.col("approx_cost") >= cost_min)
        if cost_max is not None:
            filters.append(pl.col("approx_cost") <= cost_max)

        # 3. Rating Pruning
        if query.min_rating is not None and query.min_rating > 0.0:
            filters.append((pl.col("rating") >= query.min_rating) & (pl.col("is_rated") == True))

        # 4. Cuisine Overlap Pruning (set intersection)
        if query.cuisines:
            target_cuisines = [c.lower().strip() for c in query.cuisines if c and c.strip()]
            if target_cuisines:
                # Polars expression: check if any element of target_cuisines is in cuisines array
                cuisine_exprs = [
                    pl.col("cuisines").list.contains(tc) for tc in target_cuisines
                ]
                combined_cuisine_filter = cuisine_exprs[0]
                for expr in cuisine_exprs[1:]:
                    combined_cuisine_filter = combined_cuisine_filter | expr
                filters.append(combined_cuisine_filter)

        # Apply all active filters
        filtered_df = df
        if filters:
            for f in filters:
                filtered_df = filtered_df.filter(f)

        # Deterministic sorting: popularity_score DESC, approx_cost ASC, name ASC
        sorted_df = filtered_df.sort(
            by=["popularity_score", "approx_cost", "name"],
            descending=[True, False, False],
        )

        # Brand deduplication: max_per_brand branches per chain
        candidates: list[CandidateRestaurant] = []
        brand_counts: dict[str, int] = {}
        target_limit = max(1, query.limit)

        for row in sorted_df.iter_rows(named=True):
            brand = _normalize_brand_name(row["name"])
            current_brand_count = brand_counts.get(brand, 0)
            if current_brand_count >= query.max_per_brand:
                continue

            brand_counts[brand] = current_brand_count + 1

            candidate = CandidateRestaurant(
                rest_id=row["rest_id"],
                name=row["name"],
                address=row["address"],
                location=row["location"],
                city=row["city"],
                rating=float(row["rating"]),
                is_rated=bool(row["is_rated"]),
                votes=int(row["votes"]),
                approx_cost=int(row["approx_cost"]),
                budget_tier=row["budget_tier"],
                cuisines=list(row["cuisines"]),
                primary_cuisine=row["primary_cuisine"],
                rest_type=row["rest_type"],
                highlights=list(row.get("highlights") or []),
                dish_liked_list=list(row.get("dish_liked_list") or []),
                popularity_score=float(row["popularity_score"]),
                composite_score=float(row["composite_score"]),
                url=str(row.get("url") or ""),
                online_order=str(row.get("online_order") or ""),
                book_table=str(row.get("book_table") or ""),
            )
            candidates.append(candidate)

            if len(candidates) >= target_limit:
                break

        return candidates

    def retrieve_duckdb(self, query: RetrievalQuery) -> list[CandidateRestaurant]:
        """Filter and retrieve candidates using in-memory DuckDB SQL engine.

        Args:
            query: RetrievalQuery containing filter constraints.

        Returns:
            list[CandidateRestaurant]: Filtered and ranked candidates.
        """
        where_clauses: list[str] = []
        params: list[Any] = []

        # 1. Location filter
        if query.location and not query.city_broadening:
            resolved_loc, is_city_wide = self.resolve_location(query.location)
            if not is_city_wide and resolved_loc:
                where_clauses.append("(lower(location) = lower(?) OR lower(address) LIKE ?)")
                params.append(resolved_loc)
                params.append(f"%{resolved_loc.lower()}%")

        # 2. Budget filter
        cost_min: Optional[int] = None
        cost_max: Optional[int] = None
        if query.target_cost and query.target_cost > 0:
            tol = query.cost_tolerance
            cost_min = int(round(query.target_cost * (1.0 - tol)))
            cost_max = int(round(query.target_cost * (1.0 + tol)))
        elif query.min_cost is not None or query.max_cost is not None:
            cost_min = query.min_cost
            cost_max = query.max_cost
        elif query.budget_tier:
            tier = query.budget_tier.lower().strip()
            if tier == "low":
                cost_max = settings.BUDGET_LOW_MAX
            elif tier == "medium":
                cost_min = settings.BUDGET_LOW_MAX + 1
                cost_max = settings.BUDGET_MEDIUM_MAX
            elif tier == "high":
                cost_min = settings.BUDGET_MEDIUM_MAX + 1

        if cost_min is not None:
            where_clauses.append("approx_cost >= ?")
            params.append(cost_min)
        if cost_max is not None:
            where_clauses.append("approx_cost <= ?")
            params.append(cost_max)

        # 3. Rating filter
        if query.min_rating is not None and query.min_rating > 0.0:
            where_clauses.append("rating >= ? AND is_rated = true")
            params.append(query.min_rating)

        # 4. Cuisine filter using list_has_any
        if query.cuisines:
            target_cuisines = [c.lower().strip() for c in query.cuisines if c and c.strip()]
            if target_cuisines:
                where_clauses.append("list_has_any(cuisines, ?)")
                params.append(target_cuisines)

        sql = "SELECT * FROM restaurants"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY popularity_score DESC, approx_cost ASC, name ASC"

        df_result = self._duckdb_con.execute(sql, params).df()

        # Apply brand deduplication
        candidates: list[CandidateRestaurant] = []
        brand_counts: dict[str, int] = {}
        target_limit = max(1, query.limit)

        for _, row in df_result.iterrows():
            brand = _normalize_brand_name(row["name"])
            current_brand_count = brand_counts.get(brand, 0)
            if current_brand_count >= query.max_per_brand:
                continue

            brand_counts[brand] = current_brand_count + 1

            def _to_list(val: Any) -> list[str]:
                if val is None:
                    return []
                if isinstance(val, (list, tuple)):
                    return list(val)
                if hasattr(val, "tolist"):
                    return val.tolist()
                return []

            candidate = CandidateRestaurant(
                rest_id=str(row["rest_id"]),
                name=str(row["name"]),
                address=str(row["address"]),
                location=str(row["location"]),
                city=str(row["city"]),
                rating=float(row["rating"]),
                is_rated=bool(row["is_rated"]),
                votes=int(row["votes"]),
                approx_cost=int(row["approx_cost"]),
                budget_tier=str(row["budget_tier"]),
                cuisines=_to_list(row["cuisines"]),
                primary_cuisine=str(row["primary_cuisine"]),
                rest_type=str(row["rest_type"]),
                highlights=_to_list(row.get("highlights")),
                dish_liked_list=_to_list(row.get("dish_liked_list")),
                popularity_score=float(row["popularity_score"]),
                composite_score=float(row["composite_score"]),
                url=str(row.get("url") if row.get("url") is not None else ""),
                online_order=str(row.get("online_order") if row.get("online_order") is not None else ""),
                book_table=str(row.get("book_table") if row.get("book_table") is not None else ""),
            )
            candidates.append(candidate)

            if len(candidates) >= target_limit:
                break

        return candidates

    @property
    def total_records(self) -> int:
        """Total records in the loaded dataset."""
        return self._total_records

    @property
    def unique_locations(self) -> list[str]:
        """List of all distinct localities."""
        return sorted(self._unique_locations)

    @property
    def unique_cuisines(self) -> list[str]:
        """List of all distinct cuisines."""
        return sorted(list(self._unique_cuisines))
