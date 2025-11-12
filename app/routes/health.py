"""
Health check and metrics endpoints.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Request
from app.models import HealthResponse, MetricsResponse
from app.utils.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and connectivity information.
    """
    fetcher = request.app.state.fetcher

    # Check Redis connection
    redis_connected = await fetcher.is_redis_connected()

    # Check YouTube API (simple test)
    youtube_status = "unknown"
    try:
        api_ok = await fetcher.youtube_client.test_connection()
        youtube_status = "ok" if api_ok else "error"
    except Exception as e:
        logger.error(f"YouTube API health check failed: {str(e)}")
        youtube_status = "error"

    # Get last fetch timestamp
    last_fetch = await fetcher.get_last_fetch_timestamp()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        redisConnected=redis_connected,
        lastFetch=last_fetch,
        youtubeApiStatus=youtube_status
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(request: Request) -> MetricsResponse:
    """
    Get application metrics.

    Returns request counts, cache statistics, and uptime.
    """
    fetcher = request.app.state.fetcher

    # Get last fetch timestamp
    last_fetch = await fetcher.get_last_fetch_timestamp()

    # Get metrics from collector
    metrics_data = metrics.get_metrics()

    return MetricsResponse(
        totalRequests=metrics_data["totalRequests"],
        lastFetchTimestamp=last_fetch,
        cacheHitRate=metrics_data["cacheHitRate"],
        uptimeSeconds=metrics_data["uptimeSeconds"]
    )


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "YouTube Trending Fetcher",
        "version": "1.0.0",
        "endpoints": {
            "trending": "/trending",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
        }
    }
