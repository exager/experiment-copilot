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

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Experiment Copilot backend."""

    # --- Application ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="sqlite:///./experiment.db", alias="DATABASE_URL"
    )

    # --- LLM (Google Gemini — see app/agents/llm.py) ---
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # --- LangSmith (LangChain reads the LANGCHAIN_* vars for auto-tracing) ---
    langchain_api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(
        default="experiment-copilot", alias="LANGCHAIN_PROJECT"
    )
    langchain_tracing: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")

    # --- Simulation ---
    simulation_interval_seconds: int = Field(
        default=5, alias="SIMULATION_INTERVAL_SECONDS"
    )

    # --- CORS / hosts ---
    # Accepts a JSON list (e.g. '["http://a","http://b"]'), a comma-separated
    # string ("http://a,http://b"), or "*" for wide-open (development default).
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"], alias="CORS_ORIGINS"
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["*"], alias="ALLOWED_HOSTS"
    )

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def _split_csv(cls, value):
        """Allow comma-separated env values in addition to JSON lists."""
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return ["*"]
            if v.startswith("["):
                return value  # JSON list — let pydantic parse
            return [item.strip() for item in v.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def llm_enabled(self) -> bool:
        """True when a real Gemini key is configured (else agents use a fake LLM)."""
        return bool(self.gemini_api_key)

    @property
    def langsmith_enabled(self) -> bool:
        """True when a LangSmith/LangChain API key is configured for tracing."""
        return bool(self.langchain_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
