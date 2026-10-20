"""Unit tests for configuration and project setup."""

from pathlib import Path
from src.config import Settings, settings, BASE_DIR


def test_base_dir_exists():
    """Verify BASE_DIR points to the actual project root directory."""
    assert BASE_DIR.exists()
    assert (BASE_DIR / "src").exists()
    assert (BASE_DIR / "requirements.txt").exists()


def test_default_settings():
    """Verify default settings values and types."""
    assert isinstance(settings.GROQ_MODEL, str)
    assert isinstance(settings.DEFAULT_CANDIDATE_POOL_SIZE, int)
    assert settings.DEFAULT_CANDIDATE_POOL_SIZE == 15
    assert isinstance(settings.DEFAULT_MAX_RECOMMENDATIONS, int)
    assert settings.DEFAULT_MAX_RECOMMENDATIONS == 3
    assert settings.BUDGET_LOW_MAX == 400
    assert settings.BUDGET_MEDIUM_MAX == 1200
    assert isinstance(settings.CORS_ORIGINS, list)


def test_paths_resolved_correctly():
    """Verify data paths resolve relative to BASE_DIR."""
    assert settings.DATA_DIR == BASE_DIR / "data"
    assert settings.RAW_DATA_PATH == BASE_DIR / "data" / "raw" / "zomato_raw.csv"
    assert settings.PROCESSED_DATA_PATH == BASE_DIR / "data" / "processed" / "zomato_cleaned.parquet"


def test_validation_warning_when_api_key_empty():
    """Verify warning message when GROQ_API_KEY is not configured."""
    original_key = Settings.GROQ_API_KEY
    try:
        Settings.GROQ_API_KEY = ""
        warnings = Settings.validate()
        assert len(warnings) > 0
        assert "GROQ_API_KEY" in warnings[0]
    finally:
        Settings.GROQ_API_KEY = original_key

