"""LLM orchestration, prompt engineering, and response validation modules."""

from src.llm.client import (
    # Native Groq exceptions & client
    GroqError,
    GroqAPIKeyMissingError,
    GroqTimeoutError,
    GroqAPIError,
    GroqGroundingError,
    GroqRecommenderClient,
    # Backward-compatible Gemini aliases
    GeminiError,
    GeminiAPIKeyMissingError,
    GeminiTimeoutError,
    GeminiAPIError,
    GeminiGroundingError,
    GeminiRecommenderClient,
)
from src.llm.prompts import (
    FEW_SHOT_EXAMPLES,
    SYSTEM_INSTRUCTION,
    build_recommendation_prompt,
    format_candidates_for_prompt,
)
from src.llm.schemas import (
    LLMRecommendationItem,
    LLMRecommendationOutput,
    QuerySummary,
    RecommendationResponse,
    RestaurantRecommendationItem,
    UserPreferenceRequest,
)

__all__ = [
    # Groq client
    "GroqRecommenderClient",
    "GroqError",
    "GroqAPIKeyMissingError",
    "GroqTimeoutError",
    "GroqAPIError",
    "GroqGroundingError",
    # Backward-compat aliases
    "GeminiRecommenderClient",
    "GeminiError",
    "GeminiAPIKeyMissingError",
    "GeminiTimeoutError",
    "GeminiAPIError",
    "GeminiGroundingError",
    # Prompts
    "SYSTEM_INSTRUCTION",
    "FEW_SHOT_EXAMPLES",
    "build_recommendation_prompt",
    "format_candidates_for_prompt",
    # Schemas
    "UserPreferenceRequest",
    "LLMRecommendationItem",
    "LLMRecommendationOutput",
    "QuerySummary",
    "RestaurantRecommendationItem",
    "RecommendationResponse",
]
