# Copilot instructions for spec-to-agents

Purpose: make AI coding agents productive in this FastAPI reference app that teaches agent orchestration through an event-planning domain.

Big picture
- Backend FastAPI app under `src/backend/app`. API is a 6-level learning progression: `basic_agents → agent_tools → multi_agent → workflows → orchestration → human_loop` wired in `app/api/v1/learning/router.py` and mounted in `app/main.py`.
- App startup (`app/main.py`) sets up CORS/trusted hosts, structured logging (structlog), metrics (`core/monitoring.py`), and services (Cosmos/Redis) in `lifespan`; services are on `app.state`.
- Config via Pydantic Settings in `app/core/config.py` (reads `.env`). Shared enums/models in `app/core/models.py`. Central errors/handlers in `app/core/exceptions.py`.
- Agents are scaffolded with placeholders where `agent_framework` may be missing; see `app/api/v1/learning/*` and `app/agents/specialists/event_planner.py`.

Day-to-day workflow
- From `src/backend/`: install deps with `pip install -r requirements.txt`. Quick smoke test: `python test_startup.py`. Run dev server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (docs at `/docs`, health at `/health`).
- Tests under `src/backend/tests/` (pytest, pytest-asyncio). Run from `src/backend/`: `pytest -q`.
- Settings: keep features resilient to missing Azure creds. Use `get_settings()` for config; prefer mocking external calls in tests.

Conventions to follow
- Routers: add endpoints in the right area folder (e.g., `app/api/v1/learning/*.py`) and include via that area’s `router.py`. Use tags consistent with existing levels.
- Models: prefer types in `core/models.py` (`LearningLevel`, `DifficultyLevel`, `AgentType`, `CodeExample`, etc.). Keep Level endpoints returning educational fields like `explanation`, `learning_notes`, and a `CodeExample` (see `basic_agents.py`).
- Errors/logging/metrics: raise `AgentFrameworkException` subclasses from `core/exceptions.py`; structured log with `structlog.get_logger(__name__)`; track via `MetricsCollector` on `app.state.metrics` and Prometheus helpers in `core/monitoring.py`.
- State/services: access Cosmos/Redis through `request.app.state`. If adding a new service, initialize/close it in `lifespan` like existing ones.
- Agent fallbacks: wrap `agent_framework` imports in try/except ImportError and provide mock behavior (see `basic_agents.py`, `agent_tools.py`). Keep code runnable without the framework.

Integration points (be cautious)
- Azure OpenAI/Foundry: config fields in `core/config.py`; the Foundry router is a stub (`api/v1/foundry/router.py`). Guard calls behind config and provide stubs in tests.
- Tools (Level 2): expose native functions with `@ai_function`, typed parameters, and Field metadata (`agent_tools.py`). Keep hosted/MCP tools feature-flagged via settings.

Representative files
- `app/api/v1/learning/basic_agents.py`: single-agent pattern, instruction templates, custom instructions endpoint.
- `app/api/v1/learning/agent_tools.py`: tool functions, explanation and code example generation.
- `app/agents/specialists/event_planner.py`: specialist scaffold with `DifficultyLevel` instruction sets and simple tool stubs.
- `app/core/*`: config, models, exceptions, monitoring.

Gotchas
- Run from `src/backend/` so `import app...` resolves and `.env` is picked up.
- Keep endpoints async; avoid blocking I/O in handlers.
- Maintain enum values from `core/models.py` in public APIs.

Open questions (confirm and update here)
- Package workflow: repo includes `pyproject.toml` (uv) and `src/backend/requirements.txt` (pip). Current guidance favors `src/backend` + pip for the FastAPI app; align if you standardize on `uv`.
