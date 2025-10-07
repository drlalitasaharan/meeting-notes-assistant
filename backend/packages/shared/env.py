from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Configure .env loading from the project root and ignore unknown keys
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Database (dev/test default; override in .env or env var)
    # ------------------------------------------------------------------
    DATABASE_URL: str = "sqlite:///./mna_local.db"

    # ------------------------------------------------------------------
    # App environment & simple API key for local runs
    # ------------------------------------------------------------------
    APP_ENV: str = "dev"
    API_KEY: str = "dev"

    # ------------------------------------------------------------------
    # Local filesystem (avoid Optional for Path handling)
    # ------------------------------------------------------------------
    SLIDES_DIR: str = "storage/slides"

    # ------------------------------------------------------------------
    # MinIO / S3 (canonical MinIO fields)
    # Prefer MINIO_SECURE, but accept legacy MINIO_USE_SSL and map it.
    # ------------------------------------------------------------------
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False           # canonical flag
    MINIO_USE_SSL: bool | None = None    # legacy/alias; if set, it wins

    # ------------------------------------------------------------------
    # Legacy S3-style aliases (kept for compatibility with older code)
    # Values default to the MINIO_* counterparts if not provided.
    # ------------------------------------------------------------------
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_DERIVED: Optional[str] = None  # maps to SLIDES_BUCKET by default

    # ------------------------------------------------------------------
    # Buckets
    # ------------------------------------------------------------------
    RAW_BUCKET: str = "meeting-raw"        # for meeting audio/video
    SLIDES_BUCKET: str = "meeting-slides"  # for attached slides

    # Normalize/derive after parsing
    def model_post_init(self, __context: dict[str, Any]) -> None:  # pydantic v2 hook
        # If legacy MINIO_USE_SSL is provided, use it as the canonical value
        if self.MINIO_USE_SSL is not None:
            object.__setattr__(self, "MINIO_SECURE", self.MINIO_USE_SSL)

        # Map legacy S3_* aliases from MINIO_* if not explicitly set
        if self.S3_ENDPOINT is None:
            object.__setattr__(self, "S3_ENDPOINT", self.MINIO_ENDPOINT)
        if self.S3_ACCESS_KEY is None:
            object.__setattr__(self, "S3_ACCESS_KEY", self.MINIO_ACCESS_KEY)
        if self.S3_SECRET_KEY is None:
            object.__setattr__(self, "S3_SECRET_KEY", self.MINIO_SECRET_KEY)
        if self.S3_BUCKET_DERIVED is None:
            object.__setattr__(self, "S3_BUCKET_DERIVED", self.SLIDES_BUCKET)


# Instantiate once for the whole app
settings = Settings()


def get_settings() -> Settings:
    """Convenience accessor for code expecting a callable."""
    return settings

