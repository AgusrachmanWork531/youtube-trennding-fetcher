"""
Pytest configuration and fixtures.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.youtube_client import YouTubeClient
from app.fetcher import FetcherService
from app.models import VideoData


@pytest.fixture
def mock_video_data():
    """Mock video data for testing."""
    return VideoData(
        videoId="test123",
        title="Test Video Title",
        description="This is a test video description",
        viewCount=1000000,
        publishedAt=datetime(2025, 11, 10, 12, 0, 0),
        channelTitle="Test Channel",
        channelId="UC123456",
        videoLink="https://www.youtube.com/watch?v=test123",
        thumbnailUrl="https://i.ytimg.com/vi/test123/default.jpg",
        categoryId="10",
        tags=["test", "video"]
    )


@pytest.fixture
def mock_youtube_response():
    """Mock YouTube API response."""
    return {
        "items": [
            {
                "id": "test123",
                "snippet": {
                    "title": "Test Video Title",
                    "description": "This is a test video description",
                    "publishedAt": "2025-11-10T12:00:00Z",
                    "channelTitle": "Test Channel",
                    "channelId": "UC123456",
                    "categoryId": "10",
                    "tags": ["test", "video"],
                    "thumbnails": {
                        "high": {
                            "url": "https://i.ytimg.com/vi/test123/default.jpg"
                        }
                    }
                },
                "statistics": {
                    "viewCount": "1000000"
                }
            }
        ]
    }


@pytest.fixture
def mock_youtube_client(mock_youtube_response, mock_video_data):
    """Mock YouTube client."""
    client = AsyncMock(spec=YouTubeClient)
    client.get_trending_videos = AsyncMock(return_value=[mock_video_data])
    client.search_videos = AsyncMock(return_value=[mock_video_data])
    client.get_channel_videos = AsyncMock(return_value=[mock_video_data])
    client.test_connection = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.set = AsyncMock()
    redis.ping = AsyncMock()
    redis.aclose = AsyncMock()
    return redis


@pytest.fixture
async def fetcher_service(mock_youtube_client, mock_redis_client):
    """Create fetcher service with mocked dependencies."""
    service = FetcherService(
        youtube_client=mock_youtube_client,
        redis_client=mock_redis_client
    )
    yield service
    await service.close()
