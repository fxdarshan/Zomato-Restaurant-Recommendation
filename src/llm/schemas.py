"""Data contracts and Pydantic schemas for the LLM recommendation engine."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UserPreferenceRequest(BaseModel):
    """User input request specifying dining constraints and preferences."""

    model_config = ConfigDict(extra="ignore")

    location: str = Field(
        ...,
        description="Target locality, neighborhood, or city (e.g., 'Indiranagar, Bangalore')",
        examples=["Indiranagar, Bangalore"],
    )
    budget_tier: Optional[str] = Field(
        default=None,
        description="Budget bracket: 'low' (<= Rs 400), 'medium' (Rs 401-1200), 'high' (> Rs 1200)",
        examples=["medium"],
    )
    cuisines: Optional[list[str]] = Field(
        default=None,
        description="List of desired cuisines (e.g., ['Italian', 'Continental'])",
        examples=[["Italian", "Continental"]],
    )
    min_rating: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Minimum star rating threshold (0.0 to 5.0)",
        examples=[4.0],
    )
    target_cost: Optional[int] = Field(
        default=None,
        gt=0,
        description="Optional custom target cost for two people in INR",
        examples=[1000],
    )
    vibe_and_preferences: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Freeform intent, atmosphere, or occasion (e.g. 'Quiet, romantic candle-lit spot for anniversary')",
        examples=["Quiet, candle-lit ambiance for a date night with great desserts"],
    )
    max_recommendations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of restaurants to recommend (clamped between 1 and 10, default 3)",
        examples=[3],
    )

    @field_validator("budget_tier")
    @classmethod
    def validate_budget_tier(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            normalized = v.strip().lower()
            if normalized not in ("low", "medium", "high"):
                raise ValueError("budget_tier must be one of: 'low', 'medium', 'high'")
            return normalized
        return None

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("location cannot be empty")
        return cleaned


class LLMRecommendationItem(BaseModel):
    """Output item emitted directly by Gemini model during reasoning."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    rank: int = Field(
        ...,
        ge=1,
        description="1-based recommendation rank (1 for top choice, 2 for second, etc.)",
    )
    rest_id: str = Field(
        ...,
        description="The exact rest_id of the recommended candidate from the candidate list (e.g. 'rest_00028')",
    )
    name: str = Field(
        ...,
        description="The exact name of the restaurant as provided in the candidate list",
    )
    match_badge: str = Field(
        ...,
        description="Punchy, informative badge tag (e.g. 'Best for Date Night', 'Hidden Gem', 'Value Pick')",
    )
    ai_explanation: str = Field(
        ...,
        description="Engaging 2-3 sentence explanation (35-55 words) justifying why this restaurant fits the user's vibe and preferences",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_explanation(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "ai_explanation" not in data and "explanation" in data:
                data["ai_explanation"] = data["explanation"]
            if "rest_id" not in data and "id" in data:
                data["rest_id"] = data["id"]
        return data


class LLMRecommendationOutput(BaseModel):
    """Structured JSON schema requested from Google Gemini."""

    model_config = ConfigDict(extra="ignore")

    recommendations: list[LLMRecommendationItem] = Field(
        ...,
        description="Ranked list of top recommended restaurants selected strictly from candidates",
    )
    concierge_note: str = Field(
        default="",
        description="A warm, concise 1-2 sentence culinary concierge summary for the diner",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_concierge_note(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("concierge_note"):
                data["concierge_note"] = (
                    data.get("note")
                    or data.get("summary")
                    or data.get("overview")
                    or "Handpicked based on your requested dining vibe and budget preferences."
                )
        return data


class QuerySummary(BaseModel):
    """Summary of the processed search parameters and candidate pool."""

    model_config = ConfigDict(extra="ignore")

    location: str
    budget_tier: Optional[str] = None
    target_cost: Optional[int] = None
    cuisines: Optional[list[str]] = None
    min_rating: Optional[float] = None
    vibe: Optional[str] = None
    total_candidates_analyzed: int = 0
    is_relaxed: bool = False
    relaxation_level: int = 0
    relaxation_explanation: Optional[str] = None


class RestaurantRecommendationItem(BaseModel):
    """Complete verified restaurant recommendation presented to user/client."""

    model_config = ConfigDict(extra="ignore")

    rank: int
    rest_id: str
    name: str
    location: str
    address: str
    cuisines: list[str]
    rating: float
    votes: int
    approx_cost_for_two: int
    budget_tier: str
    highlights: list[str] = Field(default_factory=list)
    ai_explanation: str
    match_badge: str
    url: str = ""
    online_order: str = ""
    book_table: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert recommendation item to dictionary."""
        return self.model_dump()


class RecommendationResponse(BaseModel):
    """Master response payload conforming to architectural specification."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(
        default="success",
        description="Status of recommendation execution ('success', 'fallback', 'no_results')",
    )
    query_summary: QuerySummary
    recommendations: list[RestaurantRecommendationItem] = Field(default_factory=list)
    concierge_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return self.model_dump()
