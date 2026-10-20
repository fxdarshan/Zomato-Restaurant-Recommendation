"""Configuration management for the AI Restaurant Recommendation System.

Supports loading from environment variables and .env files with sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

# Base project directory
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Attempt to load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
except ImportError:
    pass


class Settings:
    """Application configuration settings."""

    # ------------------------------------------------------------------ #
    # Groq LLM Settings
    # ------------------------------------------------------------------ #
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "10.0"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "400"))

    # ------------------------------------------------------------------ #
    # Storage & Data Paths
    # ------------------------------------------------------------------ #
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_PATH: Path = BASE_DIR / os.getenv("RAW_DATA_PATH", "data/raw/zomato_raw.csv")
    PROCESSED_DATA_PATH: Path = BASE_DIR / os.getenv(
        "PROCESSED_DATA_PATH", "data/processed/zomato_cleaned.parquet"
    )
    HUGGINGFACE_DATASET_ID: str = "ManikaSaini/zomato-restaurant-recommendation"

    # ------------------------------------------------------------------ #
    # API Server Settings
    # ------------------------------------------------------------------ #
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    # ------------------------------------------------------------------ #
    # Recommendation Engine Defaults
    # ------------------------------------------------------------------ #
    DEFAULT_CANDIDATE_POOL_SIZE: int = int(os.getenv("DEFAULT_CANDIDATE_POOL_SIZE", "15"))
    DEFAULT_MAX_RECOMMENDATIONS: int = int(os.getenv("DEFAULT_MAX_RECOMMENDATIONS", "3"))
    MIN_CANDIDATES_BEFORE_RELAXATION: int = int(
        os.getenv("MIN_CANDIDATES_BEFORE_RELAXATION", "5")
    )

    # ------------------------------------------------------------------ #
    # Cache Settings
    # ------------------------------------------------------------------ #
    ENABLE_QUERY_CACHE: bool = os.getenv("ENABLE_QUERY_CACHE", "true").lower() in (
        "true", "1", "yes"
    )
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # ------------------------------------------------------------------ #
    # Budget Tier Boundaries (INR for two people)
    # ------------------------------------------------------------------ #
    BUDGET_LOW_MAX: int = 400
    BUDGET_MEDIUM_MAX: int = 1200

    @classmethod
    def validate(cls) -> list[str]:
        """Validate critical configuration settings and return list of warnings."""
        warnings: list[str] = []
        if not cls.GROQ_API_KEY:
            warnings.append(
                "GROQ_API_KEY is not set. LLM recommendations will fallback to heuristic ranking."
            )
        return warnings


# Global settings singleton
settings = Settings()
