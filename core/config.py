from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"

    # Database — async driver for the app, sync driver for Alembic
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_backend"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:password@localhost:5432/ai_backend"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Connection pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def debug_sql(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
