targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
@allowed([
  'australiaeast'
  'brazilsouth'
  'canadaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'germanywestcentral'
  'italynorth'
  'japaneast'
  'koreacentral'
  'norwayeast'
  'polandcentral'
  'southafricanorth'
  'southcentralus'
  'southeastasia'
  'southindia'
  'swedencentral'
  'switzerlandnorth'
  'uaenorth'
  'uksouth'
  'westeurope'
  'westus'
  'westus2'
  'westus3'
])
@metadata({
  azd: {
    type: 'location'
  }
})
param location string

// Infrastructure resource parameters
param containerAppName string = ''
param containerRegistryName string = ''
param appUserAssignedIdentityName string = ''
param applicationInsightsName string = ''
param logAnalyticsName string = ''
param resourceGroupName string = ''

// Principal ID of the user running azd up (for development access)
param principalId string = ''

// AI Foundry parameters
@description('The name of the Azure AI Foundry resource.')
@maxLength(9)
param aiFoundryName string = 'foundry'

@description('Name for your foundry project resource.')
param projectName string = 'afproject'

@description('The description of your project.')
param projectDescription string = 'AI Agents Event Planning Application'

@description('The display name of your project.')
param projectDisplayName string = 'Event Planning Agents'

@description('The name of the Bing Grounding resource.')
param bingGroundingName string = 'bing'

// Model deployment parameters
@description('The name of the primary OpenAI model to deploy (AZURE_AI_MODEL_DEPLOYMENT_NAME)')
param modelName string = 'gpt-5-mini'

@description('The model format')
param modelFormat string = 'OpenAI'

@description('The version of the primary model. Example: 2025-08-07')
param modelVersion string = '2025-08-07'

@description('The SKU name for the model deployment')
param modelSkuName string = 'GlobalStandard'

@description('The capacity of the model deployment in TPM')
param modelCapacity int = 400

// Second model deployment parameters (for web search)
@description('The name of the secondary OpenAI model to deploy (WEB_SEARCH_MODEL)')
param webSearchModelName string = 'gpt-4.1-mini'

@description('The version of the web search model. Example: 2025-04-14')
param webSearchModelVersion string = '2025-04-14'

@description('The capacity of the web search model deployment in TPM')
param webSearchModelCapacity int = 1000

// --- Load abbreviations and generate unique names ---
var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// =================================================================
// STEP 1: DEPLOY AZURE AI FOUNDRY (SIMPLIFIED)
// Deploys AI Services account, project, and model
// =================================================================

// Deploy simplified AI Foundry with models
module aiFoundry './app/ai-foundry.bicep' = {
  name: 'ai-foundry'
  scope: rg
  params: {
    accountName: '${aiFoundryName}${resourceToken}'
    projectName: '${projectName}${resourceToken}'
    projectDescription: !empty(projectDescription) ? projectDescription : 'Event planning multi-agent system'
    projectDisplayName: !empty(projectDisplayName) ? projectDisplayName : 'Event Planning Workflow'
    modelName: modelName
    modelVersion: modelVersion
    modelFormat: modelFormat
    modelSkuName: modelSkuName
    modelCapacity: modelCapacity
    webSearchModelName: webSearchModelName
    webSearchModelVersion: webSearchModelVersion
    webSearchModelCapacity: webSearchModelCapacity
    bingAccountName: '${bingGroundingName}${resourceToken}'
    location: location
    tags: tags
  }
}

// =================================================================
// STEP 2: DEPLOY YOUR EXISTING APPLICATION INFRASTRUCTURE
// This section is mostly the same, but we will update it to use
// the new AI platform outputs.
// =================================================================

// User assigned managed identity for the app
module appUserAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: 'appUserAssignedIdentity'
  scope: rg
  params: {
    location: location
    tags: tags
    name: !empty(appUserAssignedIdentityName) ? appUserAssignedIdentityName : '${abbrs.managedIdentityUserAssignedIdentities}app-${resourceToken}'
  }
}

// Monitor application with Azure Monitor
module monitoring 'app/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: !empty(logAnalyticsName) ? logAnalyticsName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
  }
}

// Container Registry for storing Docker images
module containerRegistry './app/container-registry.bicep' = {
  name: 'acr-${resourceToken}'
  scope: rg
  params: {
    name: !empty(containerRegistryName) ? containerRegistryName : '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    tags: tags
    sku: 'Basic'
    adminUserEnabled: false
  }
}

// Grant Container Registry pull permissions to the app identity
var AcrPullRole = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
module acrRoleAssignment 'app/rbac/acr-access.bicep' = {
  name: 'acr-rbac-${resourceToken}'
  scope: rg
  params: {
    containerRegistryName: containerRegistry.outputs.name
    roleDefinitionID: AcrPullRole
    principalID: appUserAssignedIdentity.outputs.principalId
  }
}

// Grant Azure AI User role to the Container App managed identity
var AzureAIUserRole = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
module aiFoundryRoleAssignmentApp 'app/rbac/ai-foundry-access.bicep' = {
  name: 'ai-foundry-app-rbac-${resourceToken}'
  scope: rg
  params: {
    aiAccountName: aiFoundry.outputs.accountName
    roleDefinitionID: AzureAIUserRole
    principalID: appUserAssignedIdentity.outputs.principalId
  }
}

// Grant Azure AI User role to the logged-in user (for development)
module aiFoundryRoleAssignmentUser 'app/rbac/ai-foundry-access.bicep' = if (!empty(principalId)) {
  name: 'ai-foundry-user-rbac-${resourceToken}'
  scope: rg
  params: {
    aiAccountName: aiFoundry.outputs.accountName
    roleDefinitionID: AzureAIUserRole
    principalID: principalId
    principalType: 'User'
  }
}

// Unified Application - Container App with backend and frontend
module app './app/container-app.bicep' = {
  name: 'containerapp-${resourceToken}'
  scope: rg
  params: {
    name: !empty(containerAppName) ? containerAppName : '${abbrs.appContainerApps}${resourceToken}'
    location: location
    tags: tags
    serviceName: 'app' // azd service name
    resourceToken: resourceToken
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    identityId: appUserAssignedIdentity.outputs.resourceId
    containerRegistryName: containerRegistry.outputs.name
    appSettings: [
      // AI Project configuration
      {
        name: 'AZURE_AI_ACCOUNT_NAME'
        value: aiFoundry.outputs.accountName
      }
      {
        name: 'AZURE_AI_PROJECT_NAME'
        value: aiFoundry.outputs.projectName
      }
      {
        name: 'AZURE_AI_PROJECT_ENDPOINT'
        value: aiFoundry.outputs.accountEndpoint
      }
      {
        name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
        value: aiFoundry.outputs.modelDeploymentName
      }
      {
        name: 'BING_CONNECTION_NAME'
        value: aiFoundry.outputs.bingConnectionName
      }
      // Container environment settings
      {
        name: 'ENVIRONMENT'
        value: 'production'
      }
      {
        name: 'PORT'
        value: '8080'
      }
    ]
  }
  dependsOn: [
    acrRoleAssignment
    aiFoundryRoleAssignmentApp
  ]
}

// ==================================
// Outputs
// ==================================
@description('The name of the AI Foundry account.')
output AZURE_AI_ACCOUNT_NAME string = aiFoundry.outputs.accountName

@description('The name of the AI Project.')
output AZURE_AI_PROJECT_NAME string = aiFoundry.outputs.projectName

@description('The endpoint for the AI Foundry account.')
output AZURE_AI_ENDPOINT string = aiFoundry.outputs.accountEndpoint

@description('The name of the deployed model.')
output AZURE_OPENAI_DEPLOYMENT_NAME string = aiFoundry.outputs.modelDeploymentName

@description('The name of the Bing grounding connection.')
output BING_CONNECTION_NAME string = aiFoundry.outputs.bingConnectionName

@description('The resource ID of the Bing grounding connection.')
output BING_CONNECTION_ID string = aiFoundry.outputs.bingConnectionId

@description('The name of the Bing grounding account.')
output BING_ACCOUNT_NAME string = aiFoundry.outputs.bingAccountName

@description('The login server for the Azure Container Registry.')
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer

@description('Name of the deployed unified application.')
output AZURE_APP_NAME string = app.outputs.SERVICE_APP_NAME

@description('URL of the deployed unified application.')
output AZURE_APP_URI string = app.outputs.SERVICE_APP_URI

@description('The full project endpoint URL for Azure AI Foundry.')
output AZURE_AI_PROJECT_ENDPOINT string = '${aiFoundry.outputs.accountEndpoint}api/projects/${aiFoundry.outputs.projectName}'

@description('The name of the model deployment for primary agent tasks.')
output AZURE_AI_MODEL_DEPLOYMENT_NAME string = aiFoundry.outputs.modelDeploymentName

@description('The name of the web search model deployment.')
output WEB_SEARCH_MODEL string = aiFoundry.outputs.webSearchModelDeploymentName

@description('The connection string for Application Insights.')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString

@description('The Azure OpenAI API version to use.')
output AZURE_OPENAI_API_VERSION string = 'preview'
