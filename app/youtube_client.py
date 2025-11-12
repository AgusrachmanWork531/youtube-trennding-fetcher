"""
YouTube Data API v3 client with retry logic and exponential backoff.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from app.models import VideoData

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""
    pass


class YouTubeClient:
    """
    Async YouTube Data API v3 client.

    Implements:
    - Exponential backoff retry logic
    - Rate limit handling (429)
    - Proper error handling and logging
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # seconds
    MAX_BACKOFF = 60.0  # seconds

    def __init__(self, api_key: str):
        """
        Initialize YouTube API client.

        Args:
            api_key: YouTube Data API v3 key
        """
        if not api_key:
            raise ValueError("YouTube API key is required")

        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make an API request with exponential backoff retry.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            JSON response data

        Raises:
            YouTubeAPIError: If request fails after all retries
        """
        url = f"{self.BASE_URL}/{endpoint}"
        params["key"] = self.api_key

        try:
            response = await self.client.get(url, params=params)

            # Handle rate limiting (429)
            if response.status_code == 429:
                if retry_count < self.MAX_RETRIES:
                    backoff = min(
                        self.INITIAL_BACKOFF * (2 ** retry_count),
                        self.MAX_BACKOFF
                    )
                    logger.warning(
                        f"Rate limited (429). Retrying in {backoff}s "
                        f"(attempt {retry_count + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(backoff)
                    return await self._make_request(endpoint, params, retry_count + 1)
                else:
                    raise YouTubeAPIError("Rate limit exceeded. Max retries reached.")

            # Handle other errors
            if response.status_code >= 400:
                error_detail = response.json().get("error", {})
                error_message = error_detail.get("message", "Unknown error")
                logger.error(
                    f"YouTube API error {response.status_code}: {error_message}"
                )
                raise YouTubeAPIError(
                    f"YouTube API returned {response.status_code}: {error_message}"
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            if retry_count < self.MAX_RETRIES:
                backoff = min(
                    self.INITIAL_BACKOFF * (2 ** retry_count),
                    self.MAX_BACKOFF
                )
                logger.warning(
                    f"HTTP error: {str(e)}. Retrying in {backoff}s "
                    f"(attempt {retry_count + 1}/{self.MAX_RETRIES})"
                )
                await asyncio.sleep(backoff)
                return await self._make_request(endpoint, params, retry_count + 1)
            else:
                logger.error(f"HTTP error after {self.MAX_RETRIES} retries: {str(e)}")
                raise YouTubeAPIError(f"HTTP request failed: {str(e)}")

    async def get_trending_videos(
        self,
        region_code: str = "ID",
        category_id: Optional[str] = None,
        max_results: int = 10
    ) -> List[VideoData]:
        """
        Fetch trending videos from YouTube.

        Args:
            region_code: ISO 3166-1 alpha-2 country code (e.g., 'ID', 'US')
            category_id: YouTube category ID (optional)
            max_results: Maximum number of results (1-50)

        Returns:
            List of VideoData objects
        """
        max_results = min(max(1, max_results), 50)  # Clamp between 1 and 50

        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code.upper(),
            "maxResults": max_results,
        }

        if category_id:
            params["videoCategoryId"] = category_id

        logger.info(
            f"Fetching trending videos: region={region_code}, "
            f"category={category_id or 'all'}, limit={max_results}"
        )

        try:
            data = await self._make_request("videos", params)
            videos = self._parse_video_response(data)
            logger.info(f"Successfully fetched {len(videos)} trending videos")
            return videos

        except YouTubeAPIError as e:
            logger.error(f"Failed to fetch trending videos: {str(e)}")
            raise

    async def search_videos(
        self,
        query: str,
        region_code: str = "ID",
        max_results: int = 10,
        order: str = "viewCount"
    ) -> List[VideoData]:
        """
        Search for videos by keyword.

        Args:
            query: Search keyword
            region_code: ISO 3166-1 alpha-2 country code
            max_results: Maximum number of results (1-50)
            order: Sort order (date, rating, relevance, title, videoCount, viewCount)

        Returns:
            List of VideoData objects
        """
        max_results = min(max(1, max_results), 50)

        # First, search for video IDs
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "regionCode": region_code.upper(),
            "maxResults": max_results,
            "order": order,
        }

        logger.info(f"Searching videos: query='{query}', region={region_code}")

        try:
            search_data = await self._make_request("search", search_params)

            if not search_data.get("items"):
                logger.info("No videos found for search query")
                return []

            # Extract video IDs
            video_ids = [item["id"]["videoId"] for item in search_data["items"]]

            # Fetch full video details
            video_params = {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
            }

            video_data = await self._make_request("videos", video_params)
            videos = self._parse_video_response(video_data)

            logger.info(f"Successfully found {len(videos)} videos for query '{query}'")
            return videos

        except YouTubeAPIError as e:
            logger.error(f"Failed to search videos: {str(e)}")
            raise

    async def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 10
    ) -> List[VideoData]:
        """
        Fetch videos from a specific channel.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of results (1-50)

        Returns:
            List of VideoData objects
        """
        max_results = min(max(1, max_results), 50)

        # Search for videos from the channel
        search_params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": max_results,
        }

        logger.info(f"Fetching videos from channel: {channel_id}")

        try:
            search_data = await self._make_request("search", search_params)

            if not search_data.get("items"):
                logger.info(f"No videos found for channel {channel_id}")
                return []

            # Extract video IDs
            video_ids = [item["id"]["videoId"] for item in search_data["items"]]

            # Fetch full video details
            video_params = {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
            }

            video_data = await self._make_request("videos", video_params)
            videos = self._parse_video_response(video_data)

            logger.info(f"Successfully fetched {len(videos)} videos from channel")
            return videos

        except YouTubeAPIError as e:
            logger.error(f"Failed to fetch channel videos: {str(e)}")
            raise

    def _parse_video_response(self, data: Dict[str, Any]) -> List[VideoData]:
        """
        Parse YouTube API response into VideoData objects.

        Args:
            data: Raw API response

        Returns:
            List of VideoData objects
        """
        videos = []

        for item in data.get("items", []):
            try:
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})

                video = VideoData(
                    videoId=item["id"],
                    title=snippet.get("title", ""),
                    description=snippet.get("description", "")[:500],  # Truncate
                    viewCount=int(statistics.get("viewCount", 0)),
                    publishedAt=datetime.fromisoformat(
                        snippet.get("publishedAt", "").replace("Z", "+00:00")
                    ),
                    channelTitle=snippet.get("channelTitle", ""),
                    channelId=snippet.get("channelId", ""),
                    videoLink=f"https://www.youtube.com/watch?v={item['id']}",
                    thumbnailUrl=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    categoryId=snippet.get("categoryId"),
                    tags=snippet.get("tags", [])[:10]  # Limit tags
                )
                videos.append(video)

            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse video item: {str(e)}")
                continue

        return videos

    async def test_connection(self) -> bool:
        """
        Test YouTube API connection and credentials.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            params = {
                "part": "snippet",
                "chart": "mostPopular",
                "regionCode": "US",
                "maxResults": 1,
            }
            await self._make_request("videos", params)
            logger.info("YouTube API connection test successful")
            return True

        except Exception as e:
            logger.error(f"YouTube API connection test failed: {str(e)}")
            return False
