"""Application configuration via environment variables.

All settings are typed and validated at startup. Fail fast if required
secrets are missing in non-local environments.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "agentic-rag-assistant"
    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Anthropic (Claude) ---
    anthropic_api_key: str = ""
    # Default to the current most capable Opus model. Do not append date suffixes.
    claude_model: str = "claude-opus-4-8"
    claude_max_tokens: int = 4096

    # --- Embeddings (Voyage) ---
    voyage_api_key: str = ""
    voyage_model: str = "voyage-3"
    embedding_dimension: int = 1024

    # --- Vector store (Pinecone) ---
    pinecone_api_key: str = ""
    pinecone_index: str = "rag-knowledge"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # --- Web search (Tavily) ---
    tavily_api_key: str = ""
    web_search_max_results: int = 5

    # --- Ingestion ---
    max_upload_mb: int = 25
    chunk_tokens: int = 512
    chunk_overlap_tokens: int = 64

    # --- Retrieval ---
    retrieval_top_k: int = 8
    context_token_budget: int = 6000

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
