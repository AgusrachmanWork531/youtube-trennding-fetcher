"""
Tests for data models.
"""
from datetime import datetime
import pytest

from app.models import VideoData, MetaData, TrendingResponse, get_category_id_by_name


def test_video_data_creation():
    """Test VideoData model creation."""
    video = VideoData(
        videoId="abc123",
        title="Test Video",
        description="Test description",
        viewCount=1000,
        publishedAt=datetime(2025, 11, 10),
        channelTitle="Test Channel",
        channelId="UC123",
        videoLink="https://www.youtube.com/watch?v=abc123"
    )

    assert video.video_id == "abc123"
    assert video.title == "Test Video"
    assert video.view_count == 1000


def test_video_data_alias():
    """Test VideoData field aliases."""
    video = VideoData(
        videoId="abc123",
        title="Test",
        description="Test",
        viewCount=100,
        publishedAt=datetime.now(),
        channelTitle="Test",
        channelId="UC123",
        videoLink="https://test.com"
    )

    # Test model_dump with alias
    data = video.model_dump(by_alias=True)
    assert "videoId" in data
    assert "viewCount" in data


def test_metadata_creation():
    """Test MetaData model creation."""
    meta = MetaData(
        total=10,
        limit=10,
        page=1,
        fetchedAt=datetime.now(),
        fromCache=False
    )

    assert meta.total == 10
    assert meta.from_cache is False


def test_trending_response():
    """Test TrendingResponse model."""
    meta = MetaData(total=1, limit=10, page=1)
    video = VideoData(
        videoId="test",
        title="Test",
        description="Test",
        viewCount=100,
        publishedAt=datetime.now(),
        channelTitle="Test",
        channelId="UC123",
        videoLink="https://test.com"
    )

    response = TrendingResponse(meta=meta, data=[video])

    assert response.meta.total == 1
    assert len(response.data) == 1
    assert response.data[0].video_id == "test"


def test_get_category_id_by_name():
    """Test category name to ID resolution."""
    # Test exact match
    assert get_category_id_by_name("music") == "10"

    # Test case insensitive
    assert get_category_id_by_name("MUSIC") == "10"

    # Test partial match
    assert get_category_id_by_name("tech") == "28"

    # Test not found
    assert get_category_id_by_name("nonexistent") is None
