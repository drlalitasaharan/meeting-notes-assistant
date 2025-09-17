from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    API_PORT: int = 8000

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "mna"
    DB_PASSWORD: str = "mna"
    DB_NAME: str = "mna"

    OPENAI_API_KEY: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
