"""In-memory query result cache for the recommendation service.

Caches MD5 hashes of standardized query parameters to avoid redundant
Groq LLM invocations for identical requests within a configurable TTL window.

Design:
- Pure in-memory dict — no external dependencies (Redis not required).
- Thread-safe via a threading.Lock for concurrent API request safety.
- TTL expiry checked lazily on every get() call and periodically pruned.
- Cache key is MD5 of a canonical JSON representation of UserPreferenceRequest fields.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from src.llm.schemas import RecommendationResponse, UserPreferenceRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache Entry
# ---------------------------------------------------------------------------


@dataclass
class CacheEntry:
    """Single cached response entry with expiry timestamp."""

    response: RecommendationResponse
    expires_at: float  # Unix timestamp (seconds)
    created_at: float = field(default_factory=time.time)
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Return True if this cache entry has passed its TTL."""
        return time.time() > self.expires_at


# ---------------------------------------------------------------------------
# Query Cache
# ---------------------------------------------------------------------------


class QueryCache:
    """Thread-safe in-memory TTL cache for RecommendationResponse objects.

    Usage:
        cache = QueryCache(ttl_seconds=3600)
        key = cache.make_key(request)
        cached = cache.get(key)
        if cached is None:
            result = run_pipeline(...)
            cache.set(key, result)
    """

    def __init__(
        self,
        ttl_seconds: int = 3600,
        max_size: int = 512,
        enabled: bool = True,
    ) -> None:
        """Initialize the query cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds (default: 1 hour).
            max_size: Maximum number of cached entries before LRU eviction (default: 512).
            enabled: Whether caching is active. Set False to disable transparently.
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.enabled = enabled

        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._hit_count: int = 0
        self._miss_count: int = 0
        self._eviction_count: int = 0

    # ------------------------------------------------------------------
    # Key construction
    # ------------------------------------------------------------------

    @staticmethod
    def make_key(request: UserPreferenceRequest) -> str:
        """Build a deterministic MD5 cache key from the normalized request parameters.

        Normalizes by lowercasing strings and sorting list fields so that
        semantically identical queries (e.g. cuisines in different order) map
        to the same cache key.

        Args:
            request: User preference request.

        Returns:
            32-character lowercase hex MD5 digest string.
        """
        canonical: dict = {
            "location": request.location.strip().lower(),
            "budget_tier": (request.budget_tier or "").lower() or None,
            "cuisines": sorted(c.strip().lower() for c in (request.cuisines or [])) or None,
            "min_rating": request.min_rating,
            "target_cost": request.target_cost,
            "vibe_and_preferences": (request.vibe_and_preferences or "").strip().lower() or None,
            "max_recommendations": request.max_recommendations,
        }
        serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[RecommendationResponse]:
        """Retrieve a cached response by key if present and not expired.

        Args:
            key: MD5 cache key produced by make_key().

        Returns:
            Cached RecommendationResponse, or None on cache miss / expiry.
        """
        if not self.enabled:
            return None

        with self._lock:
            entry = self._store.get(key)

            if entry is None:
                self._miss_count += 1
                logger.debug("Cache MISS for key=%s", key[:8])
                return None

            if entry.is_expired():
                del self._store[key]
                self._miss_count += 1
                logger.debug("Cache EXPIRED for key=%s (age exceeded %ds TTL)", key[:8], self.ttl_seconds)
                return None

            entry.hit_count += 1
            self._hit_count += 1
            logger.debug(
                "Cache HIT for key=%s (hit_count=%d, expires_in=%.0fs)",
                key[:8],
                entry.hit_count,
                entry.expires_at - time.time(),
            )
            return entry.response

    def set(self, key: str, response: RecommendationResponse) -> None:
        """Store a RecommendationResponse under the given key with TTL.

        Evicts the oldest entry if the store is at capacity before inserting.

        Args:
            key: MD5 cache key.
            response: Validated RecommendationResponse to cache.
        """
        if not self.enabled:
            return

        with self._lock:
            # Evict oldest entry if at capacity
            if len(self._store) >= self.max_size:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
                self._eviction_count += 1
                logger.debug("Cache evicted oldest entry to maintain max_size=%d.", self.max_size)

            self._store[key] = CacheEntry(
                response=response,
                expires_at=time.time() + self.ttl_seconds,
            )
            logger.debug(
                "Cache SET key=%s (TTL=%ds, size=%d/%d)",
                key[:8],
                self.ttl_seconds,
                len(self._store),
                self.max_size,
            )

    def invalidate(self, key: str) -> bool:
        """Remove a specific entry from the cache.

        Args:
            key: Cache key to remove.

        Returns:
            True if the key existed and was removed, False otherwise.
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                logger.debug("Cache INVALIDATED key=%s", key[:8])
                return True
            return False

    def clear(self) -> int:
        """Clear all entries from the cache.

        Returns:
            Number of entries cleared.
        """
        with self._lock:
            count = len(self._store)
            self._store.clear()
            logger.info("Cache cleared: %d entries removed.", count)
            return count

    def prune_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of expired entries pruned.
        """
        with self._lock:
            expired_keys = [k for k, v in self._store.items() if v.is_expired()]
            for k in expired_keys:
                del self._store[k]
            if expired_keys:
                logger.debug("Cache pruned %d expired entries.", len(expired_keys))
            return len(expired_keys)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @property
    def stats(self) -> dict:
        """Return cache performance statistics."""
        with self._lock:
            total = self._hit_count + self._miss_count
            hit_rate = (self._hit_count / total * 100) if total > 0 else 0.0
            return {
                "enabled": self.enabled,
                "size": len(self._store),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._hit_count,
                "misses": self._miss_count,
                "evictions": self._eviction_count,
                "hit_rate_pct": round(hit_rate, 1),
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def __repr__(self) -> str:
        s = self.stats
        return (
            f"QueryCache(enabled={s['enabled']}, size={s['size']}/{s['max_size']}, "
            f"hit_rate={s['hit_rate_pct']}%, ttl={s['ttl_seconds']}s)"
        )
