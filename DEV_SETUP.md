# Development Setup Instructions

## Prerequisites

```bash
git submodule update --init --recursive

uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

# Backend

## Configuration

Add a `.env` file in the `src/spec2agent/agents` directory with the necessary environment variables for AI Foundry. You can use the `.env.example` file as a template.

## Starting DevUI

Visualize and interact with the agents using DevUI:

```bash
uv run app
```