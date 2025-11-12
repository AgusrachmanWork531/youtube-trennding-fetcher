"""
Integration tests for API routes.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.main import app
from app.fetcher import FetcherService


@pytest.fixture
def mock_fetcher_in_app(mock_youtube_client, mock_redis_client, mock_video_data):
    """Mock fetcher service and inject into app state."""
    fetcher = FetcherService(
        youtube_client=mock_youtube_client,
        redis_client=mock_redis_client
    )

    # Mock fetch_trending method
    async def mock_fetch_trending(*args, **kwargs):
        return [mock_video_data], False

    fetcher.fetch_trending = mock_fetch_trending
    fetcher.is_redis_connected = AsyncMock(return_value=True)
    fetcher.get_last_fetch_timestamp = AsyncMock(return_value=None)

    app.state.fetcher = fetcher
    return fetcher


@pytest.fixture
def client(mock_fetcher_in_app):
    """Test client with mocked dependencies."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "YouTube Trending Fetcher"


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_metrics_endpoint(client):
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "totalRequests" in data
    assert "cacheHitRate" in data


def test_trending_endpoint_default(client):
    """Test trending endpoint with default parameters."""
    response = client.get("/trending")
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert "data" in data
    assert data["meta"]["total"] >= 0


def test_trending_endpoint_with_country(client):
    """Test trending endpoint with country filter."""
    response = client.get("/trending?country=US")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_trending_endpoint_with_category(client):
    """Test trending endpoint with category filter."""
    response = client.get("/trending?category=music")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_trending_endpoint_with_keyword(client):
    """Test trending endpoint with keyword filter."""
    response = client.get("/trending?keyword=lofi")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_trending_endpoint_with_limit(client):
    """Test trending endpoint with limit parameter."""
    response = client.get("/trending?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["limit"] == 5


def test_trending_endpoint_invalid_limit(client):
    """Test trending endpoint with invalid limit."""
    response = client.get("/trending?limit=100")
    # Should clamp to max value, not error
    assert response.status_code == 200


def test_trending_endpoint_combined_filters(client):
    """Test trending endpoint with multiple filters."""
    response = client.get("/trending?country=ID&category=music&keyword=lofi&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["meta"]["limit"] == 10
