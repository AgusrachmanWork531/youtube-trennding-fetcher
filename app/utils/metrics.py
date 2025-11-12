"""
Simple metrics tracking.
"""
import time
from datetime import datetime
from typing import Optional


class MetricsCollector:
    """Basic metrics collector for the application."""

    def __init__(self):
        """Initialize metrics collector."""
        self.start_time = time.time()
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def record_request(self) -> None:
        """Record an API request."""
        self.total_requests += 1

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops == 0:
            return 0.0
        return self.cache_hits / total_cache_ops

    @property
    def uptime_seconds(self) -> float:
        """Calculate uptime in seconds."""
        return time.time() - self.start_time

    def get_metrics(self) -> dict:
        """Get all metrics as a dictionary."""
        return {
            "totalRequests": self.total_requests,
            "cacheHitRate": round(self.cache_hit_rate, 4),
            "uptimeSeconds": round(self.uptime_seconds, 2),
            "cacheHits": self.cache_hits,
            "cacheMisses": self.cache_misses,
        }


# Global metrics instance
metrics = MetricsCollector()
