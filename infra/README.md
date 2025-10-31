# Infrastructure Documentation

This directory contains the Bicep templates for deploying the spec-to-agents application to Azure.

## Overview

The infrastructure consists of:
- **Azure AI Foundry**: Hub for AI models and agents
- **Container Apps**: Hosts the web application
- **Container Registry**: Stores Docker images
- **Bing Grounding (Optional)**: Provides web search capabilities for agents
- **Monitoring**: Application Insights and Log Analytics

## Deployment

Deploy the infrastructure using Azure Developer CLI:

```bash
# Deploy everything (provision + deploy)
azd up

# Just provision infrastructure
azd provision

# Just deploy application code
azd deploy
```

## Configuration

### Bing Grounding Connection

The infrastructure includes optional support for Bing Grounding, which enables agents to perform real-time web searches.

**To enable Bing Grounding:**

Set the `BING_GROUNDING_NAME` environment variable before running `azd up`:

```bash
# Set the Bing resource name
azd env set BING_GROUNDING_NAME mybing

# Deploy the infrastructure
azd up
```

**Default behavior:**
- If `BING_GROUNDING_NAME` is not set or is empty, Bing Grounding will not be deployed
- The parameter in `main.parameters.json` has a default value of `mafbing`, which means Bing will be created unless explicitly disabled

**To disable Bing Grounding:**

```bash
# Set to empty string to skip Bing deployment
azd env set BING_GROUNDING_NAME ""

# Deploy the infrastructure
azd up
```

**What gets deployed:**
- A new Bing Grounding resource (kind: `Bing.Grounding`, SKU: `G1`)
- A connection from the AI Foundry account to the Bing resource
- The connection uses API key authentication
- Category: `GroundingWithBingSearch`

**Outputs:**
After deployment, the following outputs are available:
- `BING_GROUNDING_NAME`: Name of the Bing resource
- `BING_GROUNDING_ID`: Resource ID of the Bing resource
- `BING_CONNECTION_NAME`: Name of the connection in AI Foundry

**Using Bing Grounding in agents:**
Agents can reference the Bing connection by name (`bing-grounding`) to perform web searches. The connection is configured to allow agents to use it for grounding their responses with real-time web data.

### Other Parameters

The following parameters can be configured via environment variables:

- `AZURE_ENV_NAME`: Environment name (required)
- `AZURE_LOCATION`: Azure region (required)
- `AI_FOUNDRY_NAME`: Name prefix for AI Foundry account (default: `foundry`)
- `FOUNDRY_PROJECT_NAME`: Name prefix for AI Foundry project (default: `project`)

## File Structure

```
infra/
├── main.bicep                  # Main orchestration template
├── main.parameters.json        # Parameter mappings from environment variables
├── abbreviations.json          # Resource naming abbreviations
└── app/                        # Application-specific modules
    ├── ai-foundry.bicep        # AI Foundry account and project
    ├── bing-grounding.bicep    # Bing Grounding connection
    ├── container-app.bicep     # Container Apps environment and app
    ├── container-registry.bicep # Azure Container Registry
    └── monitoring.bicep        # Application Insights and Log Analytics
```

## Validation

To validate the Bicep templates without deploying:

```bash
cd infra
az bicep build --file main.bicep
```

Note: You may see warnings about conditional resources (BCP318, BCP422) and Bing resource types (BCP081). These are expected and do not prevent deployment.

## Troubleshooting

### Bing Grounding deployment fails

If the Bing Grounding deployment fails:
1. Ensure your subscription has the Bing resource provider registered
2. Verify that the Bing resource name is globally unique
3. Check that your subscription has quota for Bing Grounding resources

### Connection creation fails

If the connection creation fails:
1. Ensure the AI Foundry account is deployed successfully before the Bing connection
2. Check that the Bing resource is accessible and has a valid API key
3. Verify that the connection name doesn't conflict with existing connections
