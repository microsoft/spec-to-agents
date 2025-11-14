#!/bin/bash

echo "🔧 Generating .env file from infrastructure outputs..."
echo ""

# Get values from azd environment
echo "Getting environment values from azd..."
AZURE_OPENAI_API_VERSION=$(azd env get-values | grep AZURE_OPENAI_API_VERSION | cut -d'"' -f2)
AZURE_AI_PROJECT_ENDPOINT=$(azd env get-values | grep AZURE_AI_PROJECT_ENDPOINT | cut -d'"' -f2)
# Use gpt-5-mini for primary model
AZURE_AI_MODEL_DEPLOYMENT_NAME=$(azd env get-values | grep AZURE_AI_MODEL_DEPLOYMENT_NAME | cut -d'"' -f2)
# Use gpt-4.1-mini for web search model
WEB_SEARCH_MODEL=$(azd env get-values | grep WEB_SEARCH_MODEL | cut -d'"' -f2)
BING_CONNECTION_ID=$(azd env get-values | grep BING_CONNECTION_ID | cut -d'"' -f2)
APPLICATIONINSIGHTS_CONNECTION_STRING=$(azd env get-values | grep APPLICATIONINSIGHTS_CONNECTION_STRING | cut -d'"' -f2)

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp ".env" ".env.backup"
fi

# Create .env file
cat > .env << EOF
AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION
AZURE_AI_PROJECT_ENDPOINT=$AZURE_AI_PROJECT_ENDPOINT
AZURE_AI_MODEL_DEPLOYMENT_NAME=$AZURE_AI_MODEL_DEPLOYMENT_NAME
WEB_SEARCH_MODEL=$WEB_SEARCH_MODEL

# Bing Search (from Microsoft Foundry connected resources)
# TODO: Change back to BING_CONNECTION_NAME once SDK bug is fixed (currently requires full resource ID)
BING_CONNECTION_ID=$BING_CONNECTION_ID

# Calendar Storage
CALENDAR_STORAGE_PATH=./data/calendars

# A2A Agent (optional - for calendar integration)
# A2A_AGENT_HOST=http://localhost:5000

# MCP Sequential Thinking Tools
MAX_HISTORY_SIZE=1000

# OpenTelemetry Configuration
ENABLE_OTEL=true
ENABLE_SENSITIVE_DATA=true
# OTLP_ENDPOINT=http://localhost:4317
APPLICATIONINSIGHTS_CONNECTION_STRING=$APPLICATIONINSIGHTS_CONNECTION_STRING
EOF

echo ""
echo "✅ .env file generated successfully!"
echo ""
echo "📝 Configuration details:"
echo "   - Azure OpenAI API Version: $AZURE_OPENAI_API_VERSION"
echo "   - AI Project Endpoint: $AZURE_AI_PROJECT_ENDPOINT"
echo "   - Model Deployment: $AZURE_AI_MODEL_DEPLOYMENT_NAME"
echo "   - Web Search Model: $WEB_SEARCH_MODEL"
echo "   - Bing Connection ID: $BING_CONNECTION_ID"
echo ""
echo "🔐 Authentication:"
echo "   - This configuration uses Azure credential authentication (no API key)"
echo "   - Make sure you're logged in: az login"
echo "   - Required roles: 'Cognitive Services OpenAI User' or 'Cognitive Services OpenAI Contributor'"
echo ""
echo "📖 Next steps:"
echo "   1. Review the .env file and adjust settings as needed"
echo "   2. Installing dependencies with uv sync..."
echo ""

# Install dependencies with uv
echo "📦 Running uv sync..."
if uv sync; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies. You may need to run 'uv sync' manually."
    exit 1
fi

echo ""
echo "🚀 Setup complete! Run 'uv run app' to start the Agent Framework DevUI"
echo ""
