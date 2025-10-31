# GitHub Copilot Instructions

This document provides context-aware guidance for GitHub Copilot when working in this codebase.

## Project Overview

This is a Python project using **Microsoft Agent Framework** to build a multi-agent event planning workflow with the following agents:
- Event Coordinator (orchestrates overall planning)
- Venue Specialist (researches and recommends venues)
- Budget Analyst (manages costs and financial constraints)
- Catering Coordinator (handles food and beverage planning)
- Logistics Manager (coordinates schedules and resources)

## Technology Stack

- **Python 3.11+** with modern type hints and features
- **Pydantic** for data validation and settings
- **Microsoft Agent Framework** for building and orchestrating agents
- **uv** for dependency management (NOT pip/poetry/conda)
- **pytest** for testing with pytest-mock for mocking
- **Azure AI Foundry** for infrastructure (Managed Identity, no API keys)

## Project Structure

```
src/spec_to_agents/
├── agents/          # Agent definitions (budget_analyst.py, venue_specialist.py, etc.)
├── prompts/         # System prompts for each agent
├── tools/           # Reusable tool definitions
├── workflow/        # Workflow orchestration logic
└── clients.py       # Shared AI Foundry client code
```

**Important**: Each agent/workflow must have an `__init__.py` that exports the required variable (`agent` or `workflow`) to be discovered by DevUI.

## Development Commands

Use `uv` for all Python operations:
- `uv sync --dev` - Install/sync dependencies
- `uv add <package>` - Add a dependency
- `uv run pytest` - Run tests
- `uv run ruff .` - Run linting/formatting
- `uv run mypy .` - Type checking
- `uv run app` - Start Agent Framework DevUI

**Never** activate virtual environments manually - always prefix commands with `uv run`.

## Code Style Guidelines

### Python Code
- Use modern built-in type hints: `dict[str, int]`, `list[str]`, `tuple[int, ...]`
- Use `|` for unions: `str | None` instead of `Optional[str]`
- Prefer composition over large monolithic modules
- Keep modules focused on single responsibility
- Break complex functions into smaller, manageable pieces

### Documentation
- **Documentation = docstrings + type hints in code** (NOT separate markdown files)
- Use numpy-style docstrings for functions, classes, and modules
- Document WHY and HOW, not WHAT (code shows what it does)
- Skip docstrings for trivial/obvious functions
- Focus on edge cases, non-obvious behavior, and design decisions

Example docstring:
```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.

    Parameters
    ----------
    radius : float
        The radius of the circle.

    Returns
    -------
    float
        The area of the circle, calculated as π * radius^2.
    """
    import math
    return math.pi * radius ** 2
```

### Testing
- Write tests in `tests/` directory using pytest
- Use pytest-mock for mocking dependencies
- Never create throwaway test scripts - use proper test suite
- Test critical paths and edge cases (empty inputs, invalid types, large datasets)
- Include comments explaining edge cases and expected behavior

## Modularity Principles

Write highly modular code that separates concerns:
- **Testability**: Each module can be tested in isolation
- **Reusability**: Modules can be used independently
- **Maintainability**: Changes are localized to specific modules
- **Readability**: Clear separation of concerns

Keep modules focused with clear boundaries and minimal public APIs.

## Configuration

- `.env` contains Azure OpenAI config (refer to `.env.example` if missing)
- Use Managed Identity for Azure resources (no API key authentication)

## ExecPlans

For complex features or significant refactors:
1. Create specification files in `specs/` directory
2. Follow `specs/PLANS.md` format
3. For multiple specs, create a master ExecPlan linking to individual specs
4. Update `specs/README.md` with links to new specs
5. Skip ExecPlans for straightforward tasks (~25% easiest)

## Agent Framework Patterns

When working with agents:
- Each agent has associated tools and system prompts
- Tools include: Bing Search with Grounding, Weather, Calendar (ICal), Code Interpreter (Python REPL)
- Use Agent Framework DevUI (`uv run app`) for testing workflows end-to-end
- Agents are organized in a multi-agent workflow architecture

## General Development Guidelines

- Ask for clarification on unclear design decisions (human-in-the-loop)
- Explain plan before implementing large refactors
- Use existing libraries - avoid reinventing the wheel
- Prefer incremental changes with clear progress tracking
