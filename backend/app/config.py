"""Process-wide configuration bootstrap.

Two responsibilities live here:

1. Importing this module loads ``backend/.env`` into ``os.environ`` (once) so
   that env-driven settings — the ``GEMINI_API_KEY`` used by
   ``app/agents/llm.py`` and the ``LANGCHAIN_*`` variables LangChain reads for
   automatic LangSmith tracing — are available no matter which entrypoint boots
   the app. The load is idempotent and completely safe when ``.env`` is missing
   or ``python-dotenv`` is unavailable (e.g. during tests), so it never raises.

2. A pydantic-settings ``Settings`` object (via the cached ``get_settings()``)
   exposes typed application configuration for the rest of the backend.

Import this as early as possible on any code path that needs env vars. The LLM
factory (``app/agents/llm.py``) imports it at module load so every graph run has
a populated environment.
"""

from __future__ import annotations

import os

# backend/.env lives one directory above this file's package (app/ -> backend/).
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_BACKEND_DIR, ".env")

_LOADED = False


def load_env() -> bool:
    """Load ``backend/.env`` into ``os.environ`` exactly once.

    Returns ``True`` if a ``.env`` file was found and loaded, ``False`` otherwise
    (missing file or ``python-dotenv`` not installed). Never raises.
    """
    global _LOADED
    if _LOADED:
        return os.path.isfile(_ENV_PATH)
    _LOADED = True

    try:
        from dotenv import load_dotenv
    except Exception:
        # python-dotenv not installed — env may be provided by the environment.
        return False

    # Load backend/.env if present; also pick up an ambient/repo-root .env.
    # ``override=False`` keeps any already-exported real environment authoritative.
    loaded = load_dotenv(_ENV_PATH, override=False)
    load_dotenv(override=False)
    return loaded


# Load on import so a plain ``import app.config`` is enough to bootstrap env.
load_env()


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
