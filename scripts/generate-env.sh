#!/bin/bash

echo "🔧 Generating .env file from infrastructure outputs..."
echo ""

# Get values from azd environment
echo "Getting environment values from azd..."
AZURE_OPENAI_API_VERSION=$(azd env get-values | grep AZURE_OPENAI_API_VERSION | cut -d'"' -f2)
AZURE_AI_PROJECT_ENDPOINT=$(azd env get-values | grep AZURE_AI_PROJECT_ENDPOINT | cut -d'"' -f2)
AZURE_AI_MODEL_DEPLOYMENT_NAME=$(azd env get-values | grep AZURE_AI_MODEL_DEPLOYMENT_NAME | cut -d'"' -f2)
WEB_SEARCH_MODEL=$(azd env get-values | grep WEB_SEARCH_MODEL | cut -d'"' -f2)
BING_CONNECTION_NAME=$(azd env get-values | grep BING_CONNECTION_NAME | cut -d'"' -f2)
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

# Bing Search (from Azure AI Foundry connected resources)
BING_CONNECTION_NAME=$BING_CONNECTION_NAME

# Calendar Storage
CALENDAR_STORAGE_PATH=./data/calendars

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
echo "   - Bing Connection: $BING_CONNECTION_NAME"
echo ""
echo "🔐 Authentication:"
echo "   - This configuration uses Azure credential authentication (no API key)"
echo "   - Make sure you're logged in: az login"
echo "   - Required roles: 'Cognitive Services OpenAI User' or 'Cognitive Services OpenAI Contributor'"
echo ""
echo "📖 Next steps:"
echo "   1. Review the .env file and adjust settings as needed"
echo "   2. Run 'uv sync --dev' to install dependencies"
echo "   3. Run 'uv run app' to start the Agent Framework DevUI"
echo ""
