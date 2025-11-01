# PowerShell script to generate .env file from infrastructure outputs

Write-Host "🔧 Generating .env file from infrastructure outputs..." -ForegroundColor Cyan
Write-Host ""

# Get values from azd environment
Write-Host "Getting environment values from azd..."
$envValues = azd env get-values | Out-String

# Extract values using regex
$azureOpenAIApiVersion = ($envValues | Select-String 'AZURE_OPENAI_API_VERSION="([^"]*)"').Matches.Groups[1].Value
$azureAIProjectEndpoint = ($envValues | Select-String 'AZURE_AI_PROJECT_ENDPOINT="([^"]*)"').Matches.Groups[1].Value
$azureAIModelDeploymentName = ($envValues | Select-String 'AZURE_AI_MODEL_DEPLOYMENT_NAME="([^"]*)"').Matches.Groups[1].Value
$webSearchModel = ($envValues | Select-String 'WEB_SEARCH_MODEL="([^"]*)"').Matches.Groups[1].Value
$bingConnectionName = ($envValues | Select-String 'BING_CONNECTION_NAME="([^"]*)"').Matches.Groups[1].Value
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
BING_CONNECTION_NAME=$bingConnectionName

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
Write-Host "   - Bing Connection: $bingConnectionName" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔐 Authentication:" -ForegroundColor Yellow
Write-Host "   - This configuration uses Azure credential authentication (no API key)" -ForegroundColor Yellow
Write-Host "   - Make sure you're logged in: az login" -ForegroundColor Yellow
Write-Host "   - Required roles: 'Cognitive Services OpenAI User' or 'Cognitive Services OpenAI Contributor'" -ForegroundColor Yellow
Write-Host ""
Write-Host "📖 Next steps:" -ForegroundColor Green
Write-Host "   1. Review the .env file and adjust settings as needed" -ForegroundColor Green
Write-Host "   2. Run 'uv sync --dev' to install dependencies" -ForegroundColor Green
Write-Host "   3. Run 'uv run app' to start the Agent Framework DevUI" -ForegroundColor Green
Write-Host ""
