from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str

    # ------------------------------------------------------------------
    # App environment
    # ------------------------------------------------------------------
    APP_ENV: str = "dev"

    # ------------------------------------------------------------------
    # MinIO / S3
    # ------------------------------------------------------------------
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_USE_SSL: bool = False

    # ------------------------------------------------------------------
    # Buckets
    # ------------------------------------------------------------------
    RAW_BUCKET: str = "meeting-raw"        # for meeting audio/video
    SLIDES_BUCKET: str = "meeting-slides"  # for attached slides

    class Config:
        # Important: load from project root .env
        # (backend/packages/shared/env.py → up to backend → up to project root)
        env_file = Path(__file__).resolve().parents[2] / ".env"


# Instantiate once for the whole app
settings = Settings()

