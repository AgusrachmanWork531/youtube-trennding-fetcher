"""
Configuration management for the application.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # YouTube API
    youtube_api_key: str = ""

    # Default fetch settings
    default_country: str = "EN"
    default_categories: str = "music,news,tech,entertainment,gaming"
    trend_limit: int = 10

    # Scheduler settings
    scheduler_cron: str = "0 0 * * *"  # Daily at midnight
    scheduler_enabled: bool = True

    # Redis settings
    redis_url: str = "redis://redis:6379/0"
    redis_enabled: bool = True

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def categories_list(self) -> List[str]:
        """Parse default categories into a list."""
        return [c.strip() for c in self.default_categories.split(",") if c.strip()]


# Global settings instance
settings = Settings()
