# Use the official uv image as builder
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy uv cache to a predictable location for caching
ENV UV_LINK_MODE=copy

# Install dependencies first (separate layer for better caching)
# Copy only dependency files first for better layer caching
COPY uv.lock pyproject.toml README.md ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy the project source code
COPY . /app

# Sync the project itself (now including the source code)
RUN uv sync --frozen --no-dev

# Final runtime stage - use slim Python image
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install Node.js (required for MCP tools)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from the builder stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY --from=builder /app /app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV CONTAINER_ENV=true
ENV ENVIRONMENT=production

# Expose port 8080 (Azure Container Apps default)
EXPOSE 8080

# Run the application using uv run (just like locally)
CMD ["uv", "run", "app"]
