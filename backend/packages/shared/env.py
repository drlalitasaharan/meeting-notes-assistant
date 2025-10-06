from pathlib import Path

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
    # MinIO / S3
    # Prefer MINIO_SECURE, but accept legacy MINIO_USE_SSL and map it.
    # ------------------------------------------------------------------
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False           # canonical flag
    MINIO_USE_SSL: bool | None = None    # legacy/alias; if set, it wins

    # ------------------------------------------------------------------
    # Buckets
    # ------------------------------------------------------------------
    RAW_BUCKET: str = "meeting-raw"       # for meeting audio/video
    SLIDES_BUCKET: str = "meeting-slides" # for attached slides

    # Normalize legacy flag after parsing
    def model_post_init(self, __context) -> None:  # pydantic v2 hook
        if self.MINIO_USE_SSL is not None:
            # If legacy env is provided, use it as the canonical value
            object.__setattr__(self, "MINIO_SECURE", self.MINIO_USE_SSL)


# Instantiate once for the whole app
settings = Settings()

