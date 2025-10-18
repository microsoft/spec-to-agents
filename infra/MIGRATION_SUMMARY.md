# Migration Summary: Updated to Azure AI Agent Service Architecture

## Overview
Your project has been successfully updated to use the newer Azure AI Agent Service architecture from the Azure AI Foundry samples. This represents a significant architectural shift from a "bring your own application" model to a managed AI platform.

## Key Changes Made

### 1. New Directory Structure
- **Created**: `modules-standard/` directory with all required Bicep modules
- **Added**: 9 new Bicep modules for AI Agent Service infrastructure

### 2. Updated Files

#### `main.bicep`
- **Completely rewritten** to use the new AI Agent Service architecture
- **Added**: New parameters for AI Foundry resources (`aiFoundryName`, `foundryProjectName`, `aiSearchName`)
- **Replaced**: Old Azure OpenAI deployment with new AI Account and AI Project setup
- **Added**: Azure AI Search as a core dependency (previously missing)
- **Updated**: App settings to use new AI Project endpoints instead of direct Azure OpenAI

#### `main.parameters.json`
- **Added**: New parameters for AI Agent Service configuration
- **Updated**: Location restrictions to include more regions

### 3. New Modules Created

#### Core AI Infrastructure
- `ai-account-identity.bicep` - Creates the top-level AI Account
- `ai-project-identity.bicep` - Creates the AI Project and its connections
- `standard-dependent-resources.bicep` - Creates dependencies (Storage, Cosmos, AI Search)
- `add-project-capability-host.bicep` - Configures the AI Project by linking connections

#### Role Assignment Modules
- `azure-storage-account-role-assignment.bicep`
- `cosmosdb-account-role-assignment.bicep`
- `ai-search-role-assignments.bicep`
- `blob-storage-container-role-assignments.bicep`
- `cosmos-container-role-assignments.bicep`

#### Utility Modules
- `format-project-workspace-id.bicep`
- `validate-existing-resources.bicep`

## Architectural Changes

### Before (Old Architecture)
- Direct Azure OpenAI service deployment
- Function App connects directly to Azure OpenAI
- Cosmos DB managed separately
- No Azure AI Search

### After (New Architecture)
- **AI Account** as the top-level resource
- **AI Project** as a managed environment for running agents
- **Capability Hosts** that connect the project to its dependencies
- **Azure AI Search** as a core requirement for vector storage
- **Project-centric role assignments** for the AI Project's managed identity

## Application Settings Changes

### New Settings (Replacing Old Ones)
```json
{
  "AZURE_AI_ACCOUNT_NAME": "<ai-account-name>",
  "AZURE_AI_PROJECT_NAME": "<ai-project-name>", 
  "AZURE_AI_PROJECT_ENDPOINT": "<ai-account-endpoint>"
}
```

### Removed Settings
- `AZURE_OPENAI_ENDPOINT` (replaced by project endpoint)
- `EMBEDDING_MODEL_DEPLOYMENT_NAME` (models managed by project)
- `AGENTS_MODEL_DEPLOYMENT_NAME` (models managed by project)
- `COSMOS_ENDPOINT` (managed by AI project)

## Next Steps

### 1. Update Your Application Code
Your Python application code will need to be updated to use the **Azure AI Agent SDK** instead of the Azure OpenAI SDK. The new architecture uses:
- AI Project endpoints instead of direct Azure OpenAI endpoints
- Different authentication patterns
- New SDK methods for interacting with the managed AI environment

### 2. Deploy the Updated Infrastructure
```bash
# Deploy the updated infrastructure
az deployment sub create \
  --location <your-location> \
  --template-file infra/main.bicep \
  --parameters @infra/main.parameters.json
```

### 3. Update Local Development
Update your `local.settings.json` to use the new environment variables:
- `AZURE_AI_ACCOUNT_NAME`
- `AZURE_AI_PROJECT_NAME`
- `AZURE_AI_PROJECT_ENDPOINT`

## Benefits of the New Architecture

1. **Managed AI Environment**: The AI Project provides a managed environment for running agents
2. **Better Resource Management**: Centralized management of AI resources and dependencies
3. **Enhanced Security**: Project-centric role assignments and managed identities
4. **Vector Search**: Built-in Azure AI Search for vector storage and retrieval
5. **Scalability**: Better support for scaling AI workloads
6. **Future-Proof**: Aligned with Microsoft's latest AI platform direction

## Files That Were NOT Changed
- `app/api.bicep` - No changes needed (already accepts appSettings parameter)
- `app/monitoring.bicep` - No changes needed
- `app/apim.bicep` - No changes needed
- `app/dts.bicep` - No changes needed
- All RBAC modules in `app/rbac/` - No changes needed

## Important Notes

1. **Breaking Change**: This is a significant architectural change that will require application code updates
2. **New Dependencies**: Azure AI Search is now a required dependency
3. **SDK Changes**: You'll need to migrate from Azure OpenAI SDK to Azure AI Agent SDK
4. **Cost Impact**: The new architecture may have different cost implications due to additional resources
5. **Capability Hosts**: Due to Bicep type definition limitations, capability hosts are commented out in the template. You may need to configure them manually in the Azure Portal after deployment.

## Support
For questions about migrating your application code to use the new AI Agent SDK, refer to the [Azure AI Agent Service documentation](https://docs.microsoft.com/azure/ai-services/ai-agent-service/).
