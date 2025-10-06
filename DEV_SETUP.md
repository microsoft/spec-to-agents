# Development Setup Instructions

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
# For Windows (PowerShell)
$env:GIT_LFS_SKIP_SMUDGE="1"; uv sync --frozen

# For macOS/Linux
GIT_LFS_SKIP_SMUDGE=1 uv sync --frozen

cd backend/app

# For Windows (PowerShell)
$env:DEBUG="true"; uv run main.py

# For macOS/Linux
DEBUG=true uv run main.py
```

# Frontend

## Starting Frontend Server

```bash
cd frontend
npm i
npm run dev
```