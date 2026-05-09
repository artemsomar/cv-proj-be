from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "campus-navigation"
    app_env: str = "dev"
    app_debug: bool = True
    api_prefix: str = "/api/v1"
    backend_cors_origins: str = "*"

    database_url: str = ""
    alembic_database_url: str | None = None

    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
