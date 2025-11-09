# PowerShell script to generate .env file from infrastructure outputs

Write-Host "🔧 Generating .env file from infrastructure outputs..." -ForegroundColor Cyan
Write-Host ""

# Get values from azd environment
Write-Host "Getting environment values from azd..."
$envValues = azd env get-values | Out-String

# Extract values using regex
$azureOpenAIApiVersion = ($envValues | Select-String 'AZURE_OPENAI_API_VERSION="([^"]*)"').Matches.Groups[1].Value
$azureAIProjectEndpoint = ($envValues | Select-String 'AZURE_AI_PROJECT_ENDPOINT="([^"]*)"').Matches.Groups[1].Value
# Use gpt-5-mini for primary model
$azureAIModelDeploymentName = ($envValues | Select-String 'AZURE_AI_MODEL_DEPLOYMENT_NAME="([^"]*)"').Matches.Groups[1].Value
# Use gpt-4.1-mini for web search model
$webSearchModel = ($envValues | Select-String 'WEB_SEARCH_MODEL="([^"]*)"').Matches.Groups[1].Value
$bingConnectionId = ($envValues | Select-String 'BING_CONNECTION_ID="([^"]*)"').Matches.Groups[1].Value
$appInsightsConnectionString = ($envValues | Select-String 'APPLICATIONINSIGHTS_CONNECTION_STRING="([^"]*)"').Matches.Groups[1].Value

# Check if .env already exists
if (Test-Path ".env") {
    Write-Host "⚠️  .env file already exists. Backing up to .env.backup" -ForegroundColor Yellow
    Copy-Item ".env" ".env.backup" -Force
}

# Create .env file content
$envContent = @"
AZURE_OPENAI_API_VERSION=$azureOpenAIApiVersion
AZURE_AI_PROJECT_ENDPOINT=$azureAIProjectEndpoint
AZURE_AI_MODEL_DEPLOYMENT_NAME=$azureAIModelDeploymentName
WEB_SEARCH_MODEL=$webSearchModel

# Bing Search (from Azure AI Foundry connected resources)
# TODO: Change back to BING_CONNECTION_NAME once SDK bug is fixed (currently requires full resource ID)
BING_CONNECTION_ID=$bingConnectionId

# Calendar Storage
CALENDAR_STORAGE_PATH=./data/calendars

# MCP Sequential Thinking Tools
MAX_HISTORY_SIZE=1000

# OpenTelemetry Configuration
ENABLE_OTEL=true
ENABLE_SENSITIVE_DATA=true
# OTLP_ENDPOINT=http://localhost:4317
APPLICATIONINSIGHTS_CONNECTION_STRING=$appInsightsConnectionString
"@

# Write to .env file
$envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline

Write-Host ""
Write-Host "✅ .env file generated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Configuration details:" -ForegroundColor Cyan
Write-Host "   - Azure OpenAI API Version: $azureOpenAIApiVersion" -ForegroundColor Cyan
Write-Host "   - AI Project Endpoint: $azureAIProjectEndpoint" -ForegroundColor Cyan
Write-Host "   - Model Deployment: $azureAIModelDeploymentName" -ForegroundColor Cyan
Write-Host "   - Web Search Model: $webSearchModel" -ForegroundColor Cyan
Write-Host "   - Bing Connection ID: $bingConnectionId" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔐 Authentication:" -ForegroundColor Yellow
Write-Host "   - This configuration uses Azure credential authentication (no API key)" -ForegroundColor Yellow
Write-Host "   - Make sure you're logged in: az login" -ForegroundColor Yellow
Write-Host "   - Required roles: 'Cognitive Services OpenAI User' or 'Cognitive Services OpenAI Contributor'" -ForegroundColor Yellow
Write-Host ""
Write-Host "📖 Next steps:" -ForegroundColor Green
Write-Host "   1. Review the .env file and adjust settings as needed" -ForegroundColor Green
Write-Host "   2. Installing dependencies with uv sync..." -ForegroundColor Green
Write-Host ""

# Install dependencies with uv
Write-Host "📦 Running uv sync..." -ForegroundColor Cyan
try {
    uv sync
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
    } else {
        throw "uv sync failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "❌ Failed to install dependencies. You may need to run 'uv sync' manually." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Setup complete! Run 'uv run app' to start the Agent Framework DevUI" -ForegroundColor Green
Write-Host ""
