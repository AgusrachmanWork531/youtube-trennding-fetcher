"""
Fetcher service with Redis caching and deduplication logic.
"""
import json
import logging
from datetime import datetime, date
from typing import List, Optional, Tuple

import redis.asyncio as redis
from app.models import VideoData, get_category_id_by_name
from app.youtube_client import YouTubeClient, YouTubeAPIError

logger = logging.getLogger(__name__)


class FetcherService:
    """
    Service for fetching and caching YouTube trending videos.

    Features:
    - Redis caching with TTL
    - Deduplication by videoId + date
    - Fallback to cache during API failures
    - Multiple fetch strategies (trending, search, channel)
    """

    CACHE_TTL = 3600 * 24  # 24 hours
    CACHE_KEY_PREFIX = "trending"
    LAST_FETCH_KEY = "last_fetch_timestamp"

    def __init__(
        self,
        youtube_client: YouTubeClient,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize fetcher service.

        Args:
            youtube_client: YouTube API client instance
            redis_client: Redis client instance (optional)
        """
        self.youtube_client = youtube_client
        self.redis_client = redis_client
        self.cache_enabled = redis_client is not None

        if not self.cache_enabled:
            logger.warning("Redis client not provided. Caching is disabled.")

    async def close(self):
        """Close connections."""
        if self.redis_client:
            await self.redis_client.aclose()
        await self.youtube_client.close()

    def _build_cache_key(
        self,
        country: str,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        channel_id: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> str:
        """
        Build cache key from query parameters.

        Args:
            country: Country code
            category: Category name or ID
            keyword: Search keyword
            channel_id: Channel ID
            date_str: Date string (YYYY-MM-DD)

        Returns:
            Cache key string
        """
        if not date_str:
            date_str = date.today().isoformat()

        parts = [self.CACHE_KEY_PREFIX, country, date_str]

        if category:
            parts.append(f"cat_{category}")
        if keyword:
            parts.append(f"kw_{keyword}")
        if channel_id:
            parts.append(f"ch_{channel_id}")

        return ":".join(parts)

    async def _get_from_cache(self, cache_key: str) -> Optional[List[VideoData]]:
        """
        Retrieve videos from cache.

        Args:
            cache_key: Cache key

        Returns:
            List of VideoData or None if not found
        """
        if not self.cache_enabled:
            return None

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit: {cache_key}")
                videos_dict = json.loads(cached_data)
                return [VideoData(**v) for v in videos_dict]
            else:
                logger.info(f"Cache miss: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve from cache: {str(e)}")
            return None

    async def _save_to_cache(
        self,
        cache_key: str,
        videos: List[VideoData]
    ) -> None:
        """
        Save videos to cache with TTL.

        Args:
            cache_key: Cache key
            videos: List of VideoData objects
        """
        if not self.cache_enabled:
            return

        try:
            videos_dict = [v.model_dump(by_alias=True) for v in videos]
            # Convert datetime to ISO string for JSON serialization
            for video in videos_dict:
                if isinstance(video.get("publishedAt"), datetime):
                    video["publishedAt"] = video["publishedAt"].isoformat()

            await self.redis_client.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps(videos_dict, default=str)
            )
            logger.info(f"Cached {len(videos)} videos: {cache_key}")

        except Exception as e:
            logger.error(f"Failed to save to cache: {str(e)}")

    async def _update_last_fetch_timestamp(self) -> None:
        """Update the last successful fetch timestamp."""
        if not self.cache_enabled:
            return

        try:
            await self.redis_client.set(
                self.LAST_FETCH_KEY,
                datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error(f"Failed to update last fetch timestamp: {str(e)}")

    async def get_last_fetch_timestamp(self) -> Optional[datetime]:
        """Get the last successful fetch timestamp."""
        if not self.cache_enabled:
            return None

        try:
            timestamp_str = await self.redis_client.get(self.LAST_FETCH_KEY)
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str.decode())
            return None
        except Exception as e:
            logger.error(f"Failed to get last fetch timestamp: {str(e)}")
            return None

    async def fetch_trending(
        self,
        country: str = "ID",
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        channel_id: Optional[str] = None,
        limit: int = 10,
        date_str: Optional[str] = None,
        force_refresh: bool = False
    ) -> Tuple[List[VideoData], bool]:
        """
        Fetch trending videos with caching.

        Args:
            country: ISO country code
            category: Category name or ID
            keyword: Search keyword
            channel_id: Channel ID
            limit: Maximum number of results
            date_str: Date filter (YYYY-MM-DD)
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            Tuple of (videos list, from_cache boolean)
        """
        # Build cache key
        cache_key = self._build_cache_key(
            country, category, keyword, channel_id, date_str
        )

        # Try cache first (unless force refresh)
        if not force_refresh:
            cached_videos = await self._get_from_cache(cache_key)
            if cached_videos:
                return cached_videos[:limit], True

        # Determine fetch strategy
        videos = []
        category_id = None

        try:
            # Priority 1: Channel-specific videos
            if channel_id:
                logger.info(f"Fetching videos from channel: {channel_id}")
                videos = await self.youtube_client.get_channel_videos(
                    channel_id=channel_id,
                    max_results=limit
                )

            # Priority 2: Keyword search
            elif keyword:
                logger.info(f"Searching videos by keyword: {keyword}")
                videos = await self.youtube_client.search_videos(
                    query=keyword,
                    region_code=country,
                    max_results=limit
                )

            # Priority 3: Trending by category
            else:
                if category:
                    # Try to resolve category name to ID
                    category_id = get_category_id_by_name(category)
                    if not category_id:
                        # Assume it's already an ID
                        category_id = category

                logger.info(
                    f"Fetching trending videos: country={country}, "
                    f"category_id={category_id or 'all'}"
                )
                videos = await self.youtube_client.get_trending_videos(
                    region_code=country,
                    category_id=category_id,
                    max_results=limit
                )

            # Apply keyword filter if both trending and keyword are specified
            if keyword and not channel_id and videos:
                videos = self._filter_by_keyword(videos, keyword)

            # Save to cache
            if videos:
                await self._save_to_cache(cache_key, videos)
                await self._update_last_fetch_timestamp()

            return videos[:limit], False

        except YouTubeAPIError as e:
            logger.error(f"YouTube API error, trying cache fallback: {str(e)}")

            # Fallback to cache
            cached_videos = await self._get_from_cache(cache_key)
            if cached_videos:
                logger.info("Using cached data as fallback")
                return cached_videos[:limit], True

            # No cache available, re-raise error
            raise

    def _filter_by_keyword(
        self,
        videos: List[VideoData],
        keyword: str
    ) -> List[VideoData]:
        """
        Filter videos by keyword in title, description, or tags.

        Args:
            videos: List of videos
            keyword: Search keyword

        Returns:
            Filtered list of videos
        """
        keyword_lower = keyword.lower()
        filtered = []

        for video in videos:
            # Check title
            if keyword_lower in video.title.lower():
                filtered.append(video)
                continue

            # Check description
            if keyword_lower in video.description.lower():
                filtered.append(video)
                continue

            # Check tags
            if video.tags:
                for tag in video.tags:
                    if keyword_lower in tag.lower():
                        filtered.append(video)
                        break

        logger.info(
            f"Filtered {len(videos)} videos to {len(filtered)} "
            f"matching keyword '{keyword}'"
        )
        return filtered

    async def fetch_and_cache_default_categories(
        self,
        country: str,
        categories: List[str],
        limit: int = 10
    ) -> None:
        """
        Scheduled task: Fetch and cache trending videos for default categories.

        Args:
            country: ISO country code
            categories: List of category names/IDs
            limit: Number of videos per category
        """
        logger.info(
            f"Starting scheduled fetch for {country} - "
            f"categories: {', '.join(categories)}"
        )

        for category in categories:
            try:
                await self.fetch_trending(
                    country=country,
                    category=category,
                    limit=limit,
                    force_refresh=True
                )
                logger.info(
                    f"Successfully cached trending videos for: {category}")

            except Exception as e:
                logger.error(
                    f"Failed to fetch trending videos for {category}: {str(e)}"
                )

        logger.info("Scheduled fetch completed")

    async def is_redis_connected(self) -> bool:
        """Check if Redis connection is alive."""
        if not self.cache_enabled:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection check failed: {str(e)}")
            return False
