"""Application configuration loaded from environment variables.

Uses pydantic-settings so values can come from `.env` or the process
environment. A single cached `get_settings()` function is exposed so the
Settings object is constructed once per process.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Experiment Copilot backend."""

    # --- Application ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="sqlite:///./experiment.db", alias="DATABASE_URL"
    )

    # --- OpenAI ---
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # --- LangSmith ---
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(
        default="experiment-copilot", alias="LANGSMITH_PROJECT"
    )
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")

    # --- Simulation ---
    simulation_interval_seconds: int = Field(
        default=5, alias="SIMULATION_INTERVAL_SECONDS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def llm_enabled(self) -> bool:
        """True when a real LLM should be used; False falls back to MockLLM."""
        return bool(self.openai_api_key)

    @property
    def langsmith_enabled(self) -> bool:
        """True when LangSmith tracing should be activated."""
        return bool(self.langsmith_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()