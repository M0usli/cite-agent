from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (NFR-05)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cite:cite@localhost:5432/cite"
    cors_origins: list[str] = ["http://localhost:3000"]

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    tavily_api_key: str = ""

    debug_endpoints: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
