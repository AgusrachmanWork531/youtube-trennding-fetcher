"""
Tests for fetcher service.
"""
import json
import pytest
from datetime import datetime

from app.models import VideoData


@pytest.mark.asyncio
async def test_fetch_trending_without_cache(fetcher_service, mock_video_data):
    """Test fetching trending videos without cache."""
    videos, from_cache = await fetcher_service.fetch_trending(
        country="ID",
        limit=10
    )

    assert len(videos) == 1
    assert from_cache is False
    assert videos[0].video_id == "test123"


@pytest.mark.asyncio
async def test_fetch_trending_with_cache(fetcher_service, mock_video_data, mock_redis_client):
    """Test fetching trending videos from cache."""
    # Set up cache hit
    cached_data = json.dumps([mock_video_data.model_dump(by_alias=True)], default=str)
    mock_redis_client.get = pytest.AsyncMock(return_value=cached_data)

    videos, from_cache = await fetcher_service.fetch_trending(
        country="ID",
        limit=10
    )

    assert from_cache is True
    assert len(videos) == 1


@pytest.mark.asyncio
async def test_fetch_with_keyword(fetcher_service):
    """Test fetching videos with keyword search."""
    videos, from_cache = await fetcher_service.fetch_trending(
        country="ID",
        keyword="lofi",
        limit=10
    )

    assert len(videos) == 1
    assert from_cache is False


@pytest.mark.asyncio
async def test_fetch_with_channel_id(fetcher_service):
    """Test fetching videos from specific channel."""
    videos, from_cache = await fetcher_service.fetch_trending(
        country="ID",
        channel_id="UC123456",
        limit=10
    )

    assert len(videos) == 1
    assert from_cache is False


@pytest.mark.asyncio
async def test_fetch_with_category(fetcher_service):
    """Test fetching videos by category."""
    videos, from_cache = await fetcher_service.fetch_trending(
        country="ID",
        category="music",
        limit=10
    )

    assert len(videos) == 1
    assert from_cache is False


@pytest.mark.asyncio
async def test_cache_key_building(fetcher_service):
    """Test cache key generation."""
    key1 = fetcher_service._build_cache_key("ID", category="music")
    key2 = fetcher_service._build_cache_key("ID", keyword="lofi")

    assert "ID" in key1
    assert "music" in key1
    assert "lofi" in key2
    assert key1 != key2


@pytest.mark.asyncio
async def test_redis_connection_check(fetcher_service):
    """Test Redis connection check."""
    is_connected = await fetcher_service.is_redis_connected()
    assert is_connected is True


@pytest.mark.asyncio
async def test_filter_by_keyword(fetcher_service, mock_video_data):
    """Test keyword filtering."""
    videos = [mock_video_data]
    filtered = fetcher_service._filter_by_keyword(videos, "test")

    assert len(filtered) == 1

    filtered_empty = fetcher_service._filter_by_keyword(videos, "nonexistent")
    assert len(filtered_empty) == 0
