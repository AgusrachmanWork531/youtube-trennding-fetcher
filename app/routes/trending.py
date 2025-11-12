"""
Trending videos API endpoints.
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Request
from app.models import TrendingResponse, MetaData
from app.utils.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trending", tags=["trending"])


@router.get("", response_model=TrendingResponse)
async def get_trending_videos(
    request: Request,
    country: str = Query("ID", description="ISO 3166-1 alpha-2 country code"),
    category: Optional[str] = Query(None, description="Category name or ID (e.g., 'music', '10')"),
    keyword: Optional[str] = Query(None, description="Search keyword to filter videos"),
    channelId: Optional[str] = Query(None, description="YouTube channel ID", alias="channelId"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD format)"),
) -> TrendingResponse:
    """
    Get trending YouTube videos with optional filters.

    - **country**: ISO country code (default: ID)
    - **category**: Category name or ID (e.g., 'music', 'tech', '10')
    - **keyword**: Search keyword to filter videos
    - **channelId**: Specific YouTube channel ID
    - **limit**: Maximum number of results (1-50, default: 10)
    - **date**: Date filter in YYYY-MM-DD format (optional)

    Returns list of trending videos with metadata.
    """
    # Record metrics
    metrics.record_request()

    # Get fetcher service from app state
    fetcher = request.app.state.fetcher

    try:
        # Fetch videos
        videos, from_cache = await fetcher.fetch_trending(
            country=country.upper(),
            category=category,
            keyword=keyword,
            channel_id=channelId,
            limit=limit,
            date_str=date
        )

        # Record cache metrics
        if from_cache:
            metrics.record_cache_hit()
        else:
            metrics.record_cache_miss()

        # Build response
        meta = MetaData(
            total=len(videos),
            limit=limit,
            page=1,
            fetchedAt=datetime.utcnow(),
            fromCache=from_cache
        )

        return TrendingResponse(meta=meta, data=videos)

    except Exception as e:
        logger.error(f"Failed to fetch trending videos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trending videos: {str(e)}"
        )
