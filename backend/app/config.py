"""Process-wide configuration bootstrap.

Importing this module loads ``backend/.env`` into ``os.environ`` (once) so that
env-driven settings — the ``GEMINI_API_KEY`` used by ``app/agents/llm.py`` and
the ``LANGCHAIN_*`` variables LangChain reads for automatic LangSmith tracing —
are available no matter which entrypoint boots the app.

Import this as early as possible on any code path that needs env vars. The LLM
factory (``app/agents/llm.py``) imports it at module load so every graph run has
a populated environment.

The load is idempotent and completely safe when ``.env`` is missing or
``python-dotenv`` is unavailable (e.g. during tests), so it never raises.
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
