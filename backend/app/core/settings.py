from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./dev.db"
    APP_ENV: str = "dev"

    # Redis / RQ
    REDIS_URL: str = "redis://redis:6379/0"
    RQ_QUEUE: str = "default"

    # LLM
    OPENAI_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o-mini"

    # MinIO (optional)
    MINIO_ENDPOINT: str | None = None
    MINIO_ACCESS_KEY: str | None = None
    MINIO_SECRET_KEY: str | None = None
    MINIO_USE_SSL: bool = False
    SLIDES_BUCKET: str = "meeting-slides"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
