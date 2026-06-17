from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"

    # Database — async driver for the app, sync driver for Alembic
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_backend"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:password@localhost:5432/ai_backend"

    # Redis (Upstash: rediss://..., local: redis://...)
    REDIS_URL: str = "redis://localhost:6379"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Cron security — required for /cron/* HTTP endpoints
    CRON_SECRET: str = ""

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000"

    # Connection pool (reduce for Supabase transaction pooler)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 300

    # External data integrations (Phase 2)
    YOUTUBE_API_KEY: str = ""
    REDDIT_USER_AGENT: str = "ViralAI/2.0"
    HTTP_TIMEOUT: int = 20

    @model_validator(mode="after")
    def _normalise_db_urls(self) -> "Settings":
        """
        Render (and most PaaS providers) emit plain postgresql:// or postgres://
        connection strings. The app needs driver-specific prefixes:
          - asyncpg  → postgresql+asyncpg://   (used by SQLAlchemy async engine)
          - psycopg2 → postgresql+psycopg2://  (used by Alembic sync engine)
        """
        def _to_asyncpg(url: str) -> str:
            for prefix in ("postgres://", "postgresql://"):
                if url.startswith(prefix):
                    return "postgresql+asyncpg://" + url[len(prefix):]
            return url

        def _to_psycopg2(url: str) -> str:
            for prefix in ("postgres://", "postgresql://", "postgresql+asyncpg://"):
                if url.startswith(prefix):
                    return "postgresql+psycopg2://" + url[len(prefix):]
            return url

        self.DATABASE_URL = _to_asyncpg(self.DATABASE_URL)
        self.DATABASE_URL_SYNC = _to_psycopg2(self.DATABASE_URL_SYNC)
        return self

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def debug_sql(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
