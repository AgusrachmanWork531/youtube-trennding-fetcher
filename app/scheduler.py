"""
Automatic scheduler for fetching trending videos.
"""
import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.fetcher import FetcherService
from app.config import settings

logger = logging.getLogger(__name__)


class TrendingScheduler:
    """
    Scheduler for automatic trending video fetching.

    Uses APScheduler to run periodic tasks based on cron expressions.
    """

    def __init__(self, fetcher: FetcherService):
        """
        Initialize scheduler.

        Args:
            fetcher: FetcherService instance
        """
        self.fetcher = fetcher
        self.scheduler: Optional[AsyncIOScheduler] = None

    async def fetch_job(self):
        """Scheduled job to fetch and cache trending videos."""
        logger.info("Starting scheduled fetch job")

        try:
            await self.fetcher.fetch_and_cache_default_categories(
                country=settings.default_country,
                categories=settings.categories_list,
                limit=settings.trend_limit
            )
            logger.info("Scheduled fetch job completed successfully")

        except Exception as e:
            logger.error(f"Scheduled fetch job failed: {str(e)}", exc_info=True)

    def start(self):
        """Start the scheduler."""
        if not settings.scheduler_enabled:
            logger.info("Scheduler is disabled in settings")
            return

        self.scheduler = AsyncIOScheduler()

        # Parse cron expression
        # Format: minute hour day month day_of_week
        # Example: "0 0 * * *" = daily at midnight
        cron_parts = settings.scheduler_cron.split()

        if len(cron_parts) != 5:
            logger.error(
                f"Invalid cron expression: {settings.scheduler_cron}. "
                f"Expected 5 parts (minute hour day month day_of_week)"
            )
            return

        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
        )

        # Add job
        self.scheduler.add_job(
            self.fetch_job,
            trigger=trigger,
            id="fetch_trending_videos",
            name="Fetch Trending Videos",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(
            f"Scheduler started with cron: {settings.scheduler_cron}. "
            f"Next run: {self.scheduler.get_job('fetch_trending_videos').next_run_time}"
        )

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")
