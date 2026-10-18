from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (NFR-05)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cite:cite@localhost:5432/cite"
    cors_origins: list[str] = ["http://localhost:3000"]

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    tavily_api_key: str = ""

    # "bge" = local sentence-transformers model; "hashing" = no-download fake for tests/CI.
    embedding_provider: Literal["bge", "hashing"] = "bge"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Ingestion limits (FR-01) and chunking (FR-03)
    max_upload_mb: int = 20
    max_pages: int = 50
    chunk_size: int = 1000
    chunk_overlap: int = 200

    debug_endpoints: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
