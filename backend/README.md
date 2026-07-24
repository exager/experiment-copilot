# Experiment Copilot — Backend

AI-powered A/B experiment decision-support platform. FastAPI + SQLAlchemy + LangGraph.

---

## Prerequisites

- Python **3.12+**
- (Optional) A Google Gemini API key (`GEMINI_API_KEY`) — required only when the AI agents run against a real LLM. Without it, the tests and evaluation harness use a deterministic fake LLM.

---

## Setup

```bash
cd backend

# 1) Create venv + install deps
make install

# 2) Configure environment
cp .env.example .env      # then edit if you have keys

# 3) Sanity check (imports + DB init, no server)
make check

# 4) Run the API server
make run
```

Then open:
- `http://localhost:8000/health` — health check
- `http://localhost:8000/docs` — Swagger UI

The SQLite database is created at `backend/experiment.db` on first startup.

### Creating the database manually

The schema is generated directly from the SQLAlchemy models (no migrations for the
POC) via `Base.metadata.create_all()`. It runs automatically on server startup, but
you can also create it explicitly:

    cd backend

    # one-liner (Windows / PowerShell)
    ..\.venv\Scripts\python.exe -c "from app.database import init_db; init_db(); print('created experiment.db')"

    # Verify the tables were created
    ..\.venv\Scripts\python.exe -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"

This creates `backend/experiment.db` with the tables `product_contexts`,
`experiments`, `metrics`, and `report`. It is idempotent — re-running only creates
missing tables and never drops existing data.

> Note: `experiment.db` is git-ignored (via `*.db` in `.gitignore`), so the local
> database file is never committed.

---

## Environment variables

See `.env.example`. Nothing is required to boot the server; the AI keys become relevant once the LangGraph agents are wired in.

| Variable | Purpose | Required |
|---|---|---|
| `LOG_LEVEL` | Root log level | No (default `INFO`) |
| `DATABASE_URL` | SQLAlchemy URL | No (default `sqlite:///./experiment.db`) |
| `GEMINI_API_KEY` | Real LLM calls (Google Gemini) | No (fake LLM fallback) |
| `GEMINI_MODEL` | Model name | No (default `gemini-2.5-flash`) |
| `LANGCHAIN_API_KEY` | Enable LangSmith tracing | No |
| `LANGCHAIN_PROJECT` | Trace project name | No (default `experiment-copilot`) |
| `LANGCHAIN_TRACING_V2` | Explicit tracing flag | No |
| `LANGCHAIN_ENDPOINT` | LangSmith API endpoint | No |
| `SIMULATION_INTERVAL_SECONDS` | Simulator tick interval | No (default `5`) |

---

## Project layout

```
backend/
├── app/
│   ├── api/          # FastAPI routers
│   ├── agents/       # LLM agents (thin wrappers per role)
│   ├── database/     # SQLAlchemy engine, session, base
│   ├── evaluation/   # LangSmith evaluation harness
│   ├── graph/        # LangGraph workflow (state, nodes, workflow, llm)
│   ├── models/       # ORM models (ProductContext, Experiment, Metrics, Report)
│   ├── prompts/      # Prompt templates (Markdown)
│   ├── rules/        # Configurable rule engine (JSON-driven)
│   ├── schemas/      # Pydantic request/response schemas
│   ├── services/     # Domain services (thin between API and models/graph)
│   ├── simulation/   # Synthetic metric generator + APScheduler
│   ├── statistics/   # Scipy-based statistical analysis
│   ├── utils/        # Errors, helpers
│   ├── config.py     # Settings (pydantic-settings, env-driven)
│   ├── logging_config.py
│   └── main.py       # FastAPI entry point
├── tests/            # pytest suite
├── requirements.txt
├── Makefile
└── .env.example
```

---

## Makefile targets

| Target | Description |
|---|---|
| `make install` | Create `.venv/` and install pinned dependencies |
| `make run` | Run `uvicorn app.main:app --reload` on port 8000 |
| `make test` | Run `pytest` |
| `make check` | Import-time sanity check + `init_db()` |
| `make clean` | Delete venv, caches, local `*.db` |

---

## Status

Currently implemented:

- ✅ Config (`pydantic-settings`)
- ✅ Structured logging
- ✅ Custom error hierarchy
- ✅ SQLAlchemy `Base`, engine, session, `configure_database()`
- ✅ ORM models: `ProductContext`, `Experiment`, `Metrics`, `Report`
- ✅ Pydantic schemas for every resource
- ✅ FastAPI app skeleton with `/health` and `AppError` handler

In progress (see project plan):
- ⏳ Rule engine
- ⏳ Statistics engine
- ⏳ Simulation engine
- ⏳ Services layer
- ⏳ API routers
- ⏳ LangGraph workflow + agents
- ⏳ Tests