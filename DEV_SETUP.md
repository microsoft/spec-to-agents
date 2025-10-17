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

Add a `.env` file in the `backend/app` directory with the necessary environment variables.

```env
AZURE_OPENAI_BASE_URL="https://<myresource>.openai.azure.com/openai/v1/"
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=""
AZURE_OPENAI_API_VERSION="preview"
```

## Starting Backend Server

```bash
cd app

devui ./agents --port 8080
```

# Frontend

## Starting Frontend Server

```bash
cd frontend
npm i
npm run dev
```