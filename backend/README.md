# Experiment Copilot — Backend

AI-powered A/B experiment decision-support platform. FastAPI + SQLAlchemy + LangGraph.

---

## Prerequisites

- Python **3.12+**
- (Optional) An OpenAI API key — required only when the AI agents run against a real LLM. Without it, the backend will fall back to a mock LLM (once implemented).

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

---

## Environment variables

See `.env.example`. Nothing is required to boot the server; the AI keys become relevant once the LangGraph agents are wired in.

| Variable | Purpose | Required |
|---|---|---|
| `LOG_LEVEL` | Root log level | No (default `INFO`) |
| `DATABASE_URL` | SQLAlchemy URL | No (default SQLite file) |
| `OPENAI_API_KEY` | Real LLM calls | No (mock fallback) |
| `OPENAI_MODEL` | Model name | No (default `gpt-4o-mini`) |
| `LANGSMITH_API_KEY` | Enable tracing | No |
| `LANGSMITH_PROJECT` | Trace project name | No |
| `LANGSMITH_TRACING` | Explicit tracing flag | No |
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