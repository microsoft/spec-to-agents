# Copilot instructions for spec-to-agents

Purpose: make AI coding agents productive in this spec-to-agent sample that demonstrates Microsoft Agent Framework through event planning orchestration.

Big picture
- **Spec-to-Agent Sample**: Hero sample for Microsoft Agent Framework showcasing agent generation from specifications
- **Event Planning Domain**: Comprehensive event planning with multiple collaborating agents and group chat coordination
- Backend FastAPI app under `src/backend/app` with TypeScript frontend under `src/frontend` (to be built)
- **Microsoft Agent Framework**: Converged framework combining Semantic Kernel + AutoGen patterns
- **Agent Framework Integration**: Follow tier-based import patterns (Tier 0: core, Tier 1: advanced, Tier 2: connectors)
- Config via Pydantic Settings in `app/core/config.py` (reads `.env`). Shared enums/models in `app/core/models.py`. Central errors/handlers in `app/core/exceptions.py`.

Day-to-day workflow
- From `src/backend/`: install deps with `uv sync`. Run dev server: `uv run python app/main.py` (docs at `/docs`, health at `/health`).
- Tests under `src/backend/tests/` (pytest, pytest-asyncio). Run from `src/backend/`: `uv run pytest`.
- Code quality: Use `ruff` for linting/formatting, `mypy` for type checking (configured in `pyproject.toml`)
- Settings: keep features resilient to missing Azure creds. Use `get_settings()` for config; prefer mocking external calls in tests.

Conventions to follow
- **Agent Framework Patterns**: Follow Microsoft Agent Framework design principles with tier-based imports
  - Tier 0 (core): `from agent_framework import Agent, ai_function`
  - Tier 1 (advanced): `from agent_framework.workflows import WorkflowBuilder`
  - Tier 2 (connectors): `from agent_framework.azure import AzureChatClient`
- **Logging**: Use Agent Framework logging patterns with `get_logger()` instead of direct `logging.getLogger(__name__)`
- **Tools**: Create tools with `@ai_function` decorator and proper type annotations with `Annotated`
- Models: prefer types in `core/models.py` (`AgentType`, `CodeExample`, etc.). Focus on spec-to-agent generation patterns.
- Errors/logging/metrics: raise `AgentFrameworkException` subclasses from `core/exceptions.py`; use structured logging; track via `MetricsCollector` on `app.state.metrics`.
- State/services: access CosmosDB through `request.app.state`. If adding a new service, initialize/close it in `lifespan` like existing ones.
- Agent fallbacks: wrap `agent_framework` imports in try/except ImportError and provide mock behavior. Keep code runnable without the framework.

Integration points (be cautious)
- **Azure AI Services**: Use `azure-ai-projects` and `azure-ai-agents` packages instead of `azure-openai`
- **Agent Framework**: Follow tier-based import patterns and lazy loading where appropriate
- **Spec-to-Agent Generation**: Focus on generating agents from specifications and demonstrating group chat coordination
- Tools: expose native functions with `@ai_function`, typed parameters with `Annotated`, and proper descriptions

Representative files
- `app/agents/`: Agent generation and orchestration logic, following Agent Framework patterns
- `app/api/`: REST API endpoints for spec-to-agent functionality and event planning orchestration
- `app/core/*`: config, models, exceptions, monitoring following Agent Framework conventions
- `pyproject.toml`: Modern Python packaging with ruff, mypy, and pytest configuration

Gotchas
- Run from `src/backend/` so `import app...` resolves and `.env` is picked up
- Use `uv sync` and `uv run` commands for dependency management and execution
- Keep endpoints async; avoid blocking I/O in handlers
- Follow Agent Framework logging patterns with `get_logger()` instead of direct logging imports
- Use proper type annotations with `Annotated` for tool parameters

Development focus
- **Spec-to-Agent**: Demonstrate generating specialized agents from specifications
- **Group Chat**: Showcase multi-agent coordination and real-time collaboration
- **Event Planning**: Use relatable domain to demonstrate complex orchestration patterns
- **Agent Framework Integration**: Follow Microsoft Agent Framework design principles and patterns
