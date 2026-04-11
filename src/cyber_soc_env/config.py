"""Configuration module using pydantic-settings and python-dotenv."""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key",
    )

    # Environment
    env_mode: str = Field(
        default_factory=lambda: os.getenv("ENV_MODE", "development"),
        description="Environment mode",
    )
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level",
    )

    # API
    api_host: str = Field(
        default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"),
        description="API server host",
    )
    api_port: int = Field(
        default_factory=lambda: int(os.getenv("API_PORT", "8000")),
        description="API server port",
    )

    # Docker
    docker_host: str = Field(
        default_factory=lambda: os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock"),
        description="Docker daemon socket",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
