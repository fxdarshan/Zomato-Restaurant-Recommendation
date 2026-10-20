"""Client adapter for communicating with the Restaurant Recommendation engine.

Supports dual-mode execution:
1. REST Mode: Communicates with FastAPI via HTTP endpoints (/health, /api/v1/metadata, /api/v1/recommend).
2. Direct Mode: Seamlessly falls back to direct Python invocation of RecommenderService if the API server is unreachable.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests

from src.llm.schemas import RecommendationResponse, UserPreferenceRequest

logger = logging.getLogger(__name__)

DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class RecommenderUIClient:
    """Unified client for Streamlit UI with automatic fallback between REST and Direct service."""

    def __init__(self, api_base_url: str = DEFAULT_API_BASE_URL):
        self.api_base_url = api_base_url.rstrip("/")
        self._direct_service = None
        self._is_server_available: Optional[bool] = None

    def _get_direct_service(self):
        """Lazy-initialize direct Python RecommenderService."""
        if self._direct_service is None:
            from src.services.recommender import RecommenderService
            self._direct_service = RecommenderService()
        return self._direct_service

    def check_connection(self) -> dict[str, Any]:
        """Check if FastAPI server is responsive; returns status info."""
        try:
            resp = requests.get(f"{self.api_base_url}/health", timeout=1.5)
            if resp.status_code == 200:
                self._is_server_available = True
                data = resp.json()
                data["mode"] = "REST API"
                data["endpoint"] = self.api_base_url
                return data
        except Exception:
            pass

        self._is_server_available = False
        svc = self._get_direct_service()
        retriever = svc.relaxation_engine.retriever
        return {
            "status": "healthy",
            "mode": "Direct In-Process Engine",
            "service": "AI Restaurant Recommendation Engine",
            "version": "1.0.0",
            "dataset_loaded": True,
            "total_records": retriever.total_records,
            "llm_configured": svc.llm_client.is_configured,
            "groq_model": getattr(svc.llm_client, "model", "Groq LPU"),
            "cache_stats": svc.get_cache_stats(),
        }

    def get_metadata(self) -> dict[str, Any]:
        """Fetch metadata for dropdown filters (locations, cuisines, budget tiers)."""
        if self._is_server_available is not False:
            try:
                resp = requests.get(f"{self.api_base_url}/api/v1/metadata", timeout=2.0)
                if resp.status_code == 200:
                    self._is_server_available = True
                    return resp.json()
            except Exception:
                self._is_server_available = False

        # Direct Mode fallback
        svc = self._get_direct_service()
        retriever = svc.relaxation_engine.retriever
        from src.config import settings
        return {
            "locations": retriever.unique_locations,
            "cuisines": retriever.unique_cuisines,
            "budget_tiers": [
                {
                    "value": "low",
                    "label": "Budget Friendly",
                    "description": f"Up to ₹{settings.BUDGET_LOW_MAX} for two",
                    "max_cost": settings.BUDGET_LOW_MAX,
                },
                {
                    "value": "medium",
                    "label": "Mid Range",
                    "description": f"₹{settings.BUDGET_LOW_MAX + 1}–₹{settings.BUDGET_MEDIUM_MAX} for two",
                    "min_cost": settings.BUDGET_LOW_MAX + 1,
                    "max_cost": settings.BUDGET_MEDIUM_MAX,
                },
                {
                    "value": "high",
                    "label": "Premium",
                    "description": f"Above ₹{settings.BUDGET_MEDIUM_MAX} for two",
                    "min_cost": settings.BUDGET_MEDIUM_MAX + 1,
                },
            ],
            "total_restaurants": retriever.total_records,
        }

    def recommend(self, req: UserPreferenceRequest) -> tuple[RecommendationResponse, float, str]:
        """Request recommendations; returns (RecommendationResponse, latency_ms, mode_used)."""
        start = time.perf_counter()

        # Try REST endpoint first
        if self._is_server_available is not False:
            try:
                resp = requests.post(
                    f"{self.api_base_url}/api/v1/recommend",
                    json=req.model_dump(),
                    timeout=30.0,
                )
                if resp.status_code == 200:
                    elapsed = (time.perf_counter() - start) * 1000
                    parsed = RecommendationResponse.model_validate(resp.json())
                    self._is_server_available = True
                    return parsed, elapsed, "REST API"
            except Exception as e:
                logger.warning("REST call failed, switching to direct engine: %s", e)
                self._is_server_available = False

        # Direct Mode execution
        svc = self._get_direct_service()
        response = svc.recommend(req)
        elapsed = (time.perf_counter() - start) * 1000
        return response, elapsed, "Direct Engine"
