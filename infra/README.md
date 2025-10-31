# Infrastructure Overview

This directory contains Azure Bicep templates for deploying the Event Planning Agents application infrastructure.

## Architecture

The infrastructure is organized into modular Bicep templates:

### Main Template (`main.bicep`)

The main orchestration template that deploys all resources:

1. **Azure AI Foundry** - AI Services account with project and model deployment
2. **Bing Grounding** - Web search capabilities for real-time information
3. **Container Registry** - Docker image storage
4. **Managed Identity** - Authentication for the application
5. **Application Insights** - Monitoring and telemetry
6. **Container App** - Hosting for the application

### Module Templates (`app/`)

Specialized modules for each service:

- `ai-foundry.bicep` - AI Services account, project, and model deployment
- `bing-grounding.bicep` - Bing Grounding resource and AI Foundry connection
- `container-registry.bicep` - Azure Container Registry
- `container-app.bicep` - Azure Container App with environment
- `monitoring.bicep` - Application Insights and Log Analytics

## Bing Grounding Integration

The Bing Grounding connection enables agents to perform web searches for real-time information.

### How it works

1. **Resource Creation**: A Bing Grounding resource is created with SKU `G1` (Grounding with Bing Search)
2. **Connection Setup**: An API key-based connection named `bing-grounding` is created in the AI Foundry account
3. **Environment Variables**: The connection name is passed to the Container App via `BING_CONNECTION_NAME`
4. **Agent Usage**: Agents use the `HostedWebSearchTool` which automatically uses this connection

### Configuration

The Bing resource is deployed with:
- **Location**: `global` (standard for Bing resources)
- **SKU**: `G1` (Grounding with Bing Search)
- **Kind**: `Bing.Grounding`
- **Connection Name**: `bing-grounding` (hardcoded in the module)

### Customization

To use a custom Bing resource name, set the `bingResourceName` parameter:

```bash
azd provision --parameter bingResourceName=my-bing-resource
```

If not specified, a name is automatically generated using the pattern: `bing-{resourceToken}`

## Deployment

### Using Azure Developer CLI (azd)

Deploy all infrastructure:

```bash
azd up
```

Or deploy infrastructure only:

```bash
azd provision
```

### Parameters

Key parameters that can be customized:

- `environmentName` - Environment identifier (required)
- `location` - Azure region (required)
- `aiFoundryName` - AI Foundry account name prefix (default: `foundry`)
- `projectName` - AI Foundry project name prefix (default: `project`)
- `bingResourceName` - Custom Bing resource name (optional)
- `modelName` - OpenAI model to deploy (default: `gpt-4o`)
- `modelVersion` - Model version (default: `2024-11-20`)

### Outputs

The deployment provides these outputs:

- `AZURE_AI_ACCOUNT_NAME` - AI Foundry account name
- `AZURE_AI_PROJECT_NAME` - AI Foundry project name
- `AZURE_AI_ENDPOINT` - AI Foundry endpoint URL
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Deployed model name
- `BING_RESOURCE_NAME` - Bing Grounding resource name
- `BING_CONNECTION_NAME` - Bing connection name (always `bing-grounding`)
- `AZURE_CONTAINER_REGISTRY_ENDPOINT` - Container registry login server
- `AZURE_APP_NAME` - Deployed application name
- `AZURE_APP_URI` - Application URL

## Testing the Deployment

After deployment, verify the Bing connection:

1. Navigate to the Azure Portal
2. Open your AI Foundry account
3. Go to "Connections" under Settings
4. Verify the `bing-grounding` connection exists
5. Check that it's configured with ApiKey authentication

Test the application:

```bash
# Get the application URL
azd show

# Visit the URL and test web search functionality
# The Venue Specialist and Catering Coordinator agents use Bing search
```

## Troubleshooting

### Bing Connection Not Found

If agents report that the Bing connection is not found:

1. Check that the `BING_CONNECTION_NAME` environment variable is set correctly
2. Verify the connection exists in the AI Foundry account
3. Ensure the Container App has been restarted after infrastructure updates

### Web Search Failures

If web searches fail:

1. Verify the Bing resource is active in Azure Portal
2. Check the Bing resource's API keys are valid
3. Review Application Insights logs for detailed error messages

## Production Considerations

For production deployments, consider:

1. **Cost Management**: Bing Grounding has per-request costs - monitor usage
2. **Rate Limits**: Configure appropriate rate limiting for web search requests
3. **Caching**: Implement caching for frequently searched queries
4. **Fallback**: Handle scenarios where web search is unavailable

## References

- [Bing Grounding Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
