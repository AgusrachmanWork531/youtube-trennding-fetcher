"""
Data models for YouTube Trending Fetcher service.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class VideoData(BaseModel):
    """Model representing a single YouTube video."""
    video_id: str = Field(..., alias="videoId")
    title: str
    description: str
    view_count: int = Field(..., alias="viewCount")
    published_at: datetime = Field(..., alias="publishedAt")
    channel_title: str = Field(..., alias="channelTitle")
    channel_id: str = Field(..., alias="channelId")
    video_link: str = Field(..., alias="videoLink")
    thumbnail_url: Optional[str] = Field(None, alias="thumbnailUrl")
    category_id: Optional[str] = Field(None, alias="categoryId")
    tags: Optional[List[str]] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "videoId": "abc123xyz",
                "title": "Amazing Video Title",
                "description": "This is an amazing video...",
                "viewCount": 1234567,
                "publishedAt": "2025-11-10T12:34:56Z",
                "channelTitle": "Cool Channel",
                "channelId": "UCxxxxxxx",
                "videoLink": "https://www.youtube.com/watch?v=abc123xyz",
                "thumbnailUrl": "https://i.ytimg.com/vi/abc123xyz/default.jpg",
                "categoryId": "10",
                "tags": ["music", "lofi", "chill"]
            }
        }


class MetaData(BaseModel):
    """Pagination and metadata information."""
    total: int
    limit: int
    page: int
    fetched_at: Optional[datetime] = Field(None, alias="fetchedAt")
    from_cache: bool = Field(False, alias="fromCache")

    class Config:
        populate_by_name = True


class TrendingResponse(BaseModel):
    """Response model for trending videos endpoint."""
    meta: MetaData
    data: List[VideoData]

    class Config:
        json_schema_extra = {
            "example": {
                "meta": {
                    "total": 10,
                    "limit": 10,
                    "page": 1,
                    "fetchedAt": "2025-11-12T10:00:00Z",
                    "fromCache": False
                },
                "data": []
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    redis_connected: bool = Field(..., alias="redisConnected")
    last_fetch: Optional[datetime] = Field(None, alias="lastFetch")
    youtube_api_status: str = Field(..., alias="youtubeApiStatus")

    class Config:
        populate_by_name = True


class MetricsResponse(BaseModel):
    """Metrics endpoint response model."""
    total_requests: int = Field(..., alias="totalRequests")
    last_fetch_timestamp: Optional[datetime] = Field(None, alias="lastFetchTimestamp")
    cache_hit_rate: float = Field(..., alias="cacheHitRate")
    uptime_seconds: float = Field(..., alias="uptimeSeconds")

    class Config:
        populate_by_name = True


class YouTubeCategory(BaseModel):
    """YouTube video category mapping."""
    id: str
    name: str


# YouTube category mappings (most common ones)
YOUTUBE_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Documentary",
    "35": "Drama",
    "36": "Family",
    "37": "Foreign",
    "38": "Horror",
    "39": "Sci-Fi/Fantasy",
    "40": "Thriller",
    "41": "Shorts",
    "42": "Shows",
    "43": "Trailers",
    "44": "Tech",
}


def get_category_id_by_name(category_name: str) -> Optional[str]:
    """Get category ID by name (case-insensitive partial match)."""
    category_lower = category_name.lower()
    for cat_id, cat_name in YOUTUBE_CATEGORIES.items():
        if category_lower in cat_name.lower():
            return cat_id
    return None
