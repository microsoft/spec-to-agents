# Development Setup Instructions

## Starting Backend Server

```bash
cd backend/app
# For Windows (PowerShell)
$env:DEBUG="true"; uv run main.py

# For macOS/Linux
DEBUG=true uv run main.py
```

## Starting Frontend Server

```bash
cd frontend
npm i
npm run dev
```