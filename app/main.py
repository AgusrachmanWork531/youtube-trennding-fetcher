"""
Main FastAPI application for YouTube Trending Fetcher.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from app.config import settings
from app.utils.logger import setup_logging
from app.youtube_client import YouTubeClient
from app.fetcher import FetcherService
from app.scheduler import TrendingScheduler
from app.routes import trending, health

# Setup logging
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting YouTube Trending Fetcher service")

    # Validate YouTube API key
    if not settings.youtube_api_key:
        logger.error("YOUTUBE_API_KEY is not set!")
        raise ValueError("YOUTUBE_API_KEY environment variable is required")

    # Initialize YouTube client
    youtube_client = YouTubeClient(api_key=settings.youtube_api_key)
    logger.info("YouTube client initialized")

    # Initialize Redis client (optional)
    redis_client = None
    if settings.redis_enabled:
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            logger.info(f"Redis connected: {settings.redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Caching disabled.")
            redis_client = None

    # Initialize fetcher service
    fetcher = FetcherService(
        youtube_client=youtube_client,
        redis_client=redis_client
    )
    logger.info("Fetcher service initialized")

    # Store in app state
    app.state.fetcher = fetcher

    # Initialize and start scheduler
    scheduler = TrendingScheduler(fetcher)
    scheduler.start()
    app.state.scheduler = scheduler

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down YouTube Trending Fetcher service")

    # Stop scheduler
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()

    # Close connections
    if hasattr(app.state, "fetcher"):
        await app.state.fetcher.close()

    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="YouTube Trending Fetcher",
    description=(
        "A microservice for fetching and caching trending YouTube videos "
        "with support for filtering by country, category, keywords, and channels."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(trending.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
    )
