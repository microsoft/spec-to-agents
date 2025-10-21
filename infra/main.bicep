targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
@allowed([ 'eastus2', 'westus', 'westus2', 'westus3', 'eastus', 'uksouth', 'swedencentral', 'australiaeast', 'japaneast'])
@metadata({
  azd: {
    type: 'location'
  }
})
param location string

// Parameters for your existing application resources
param apiServiceName string = ''
param frontendServiceName string = ''
param apiUserAssignedIdentityName string = ''
param frontendUserAssignedIdentityName string = ''
param applicationInsightsName string = ''
param logAnalyticsName string = ''
param resourceGroupName string = ''
param storageAccountName string = ''
param dtsSkuName string = 'Dedicated'
param dtsName string = ''
param taskHubName string = ''
param apimServiceName string = ''
param apimPublisherName string = 'spec-to-agents API'
param apimPublisherEmail string = 'admin@contoso.com'

// App registration parameters
param appRegistrationClientId string = ''

// --- NEW PARAMETERS FOR AZURE AI AGENT SERVICE ---
@description('The name of the Azure AI Foundry resource.')
param aiFoundryName string = 'foundry'

@description('Name for your foundry project resource.')
param foundryProjectName string = 'project'

@description('A short name for the new AI Search service that will be created.')
param aiSearchName string = ''

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
// STEP 1: DEPLOY AZURE AI AGENT SERVICE (FOUNDRY) INFRASTRUCTURE
// This section uses the new modules to create the core AI platform.
// =================================================================

// Generate unique names for AI platform dependencies
var aiAccountName = toLower('${aiFoundryName}${resourceToken}')
var aiProjectName = toLower('${foundryProjectName}${resourceToken}')
var aiCosmosDBName = toLower('${resourceToken}aicosmosdb')
var aiSearchActualName = !empty(aiSearchName) ? aiSearchName : toLower('${resourceToken}aisearch')
var aiStorageName = toLower('${resourceToken}aistorage')

// Module to create the core dependencies for the AI Project (Storage, Cosmos, AI Search)
// We are creating new resources here, but this module supports bringing your own.
module aiDependencies 'modules-standard/standard-dependent-resources.bicep' = {
  name: 'ai-dependencies'
  scope: rg
  params: {
    location: location
    azureStorageName: aiStorageName
    aiSearchName: aiSearchActualName
    cosmosDBName: aiCosmosDBName
    tags: tags
    // We are creating new resources, so 'Exists' flags are false
    aiSearchExists: false
    azureStorageExists: false
    cosmosDBExists: false
    // Setting resource IDs to empty since we are not bringing existing resources
    aiSearchResourceId: ''
    azureStorageAccountResourceId: ''
    cosmosDBResourceId: ''
  }
}

// Module to create the top-level AI Account
module aiAccount 'modules-standard/ai-account-identity.bicep' = {
  name: 'ai-account'
  scope: rg
  params: {
    accountName: aiAccountName
    location: location
  }
}

// Module to create the AI Project under the AI Account
module aiProject 'modules-standard/ai-project-identity.bicep' = {
  name: 'ai-project'
  scope: rg
  params: {
    accountName: aiAccount.outputs.accountName
    projectName: aiProjectName
    projectDescription: 'AI Project for the spec-to-agents Application'
    displayName: aiProjectName
    location: location
    // Wire up the dependencies created in the previous step
    aiSearchName: aiDependencies.outputs.aiSearchName
    aiSearchServiceResourceGroupName: aiDependencies.outputs.aiSearchServiceResourceGroupName
    aiSearchServiceSubscriptionId: aiDependencies.outputs.aiSearchServiceSubscriptionId
    cosmosDBName: aiDependencies.outputs.cosmosDBName
    cosmosDBSubscriptionId: aiDependencies.outputs.cosmosDBSubscriptionId
    cosmosDBResourceGroupName: aiDependencies.outputs.cosmosDBResourceGroupName
    azureStorageName: aiDependencies.outputs.azureStorageName
    azureStorageSubscriptionId: aiDependencies.outputs.azureStorageSubscriptionId
    azureStorageResourceGroupName: aiDependencies.outputs.azureStorageResourceGroupName
    // We are not bringing an existing AOAI resource in this setup
    aoaiPassedIn: false
    existingAoaiName: ''
    existingAoaiSubscriptionId: ''
    existingAoaiResourceGroupName: ''
  }
}

module formatProjectWorkspaceId 'modules-standard/format-project-workspace-id.bicep' = {
  name: 'format-project-workspace-id'
  scope: rg
  params: {
    projectWorkspaceId: aiProject.outputs.projectWorkspaceId
  }
}

// --- Granting Permissions for the AI Project ---
// The AI Project's managed identity needs permissions on its dependencies.

module storageAccountRoleAssignment 'modules-standard/azure-storage-account-role-assignment.bicep' = {
  name: 'ai-storage-role-assignment'
  scope: rg
  params: {
    azureStorageName: aiDependencies.outputs.azureStorageName
    projectPrincipalId: aiProject.outputs.projectPrincipalId
  }
}

module cosmosAccountRoleAssignments 'modules-standard/cosmosdb-account-role-assignment.bicep' = {
  name: 'ai-cosmos-role-assignment'
  scope: rg
  params: {
    cosmosDBName: aiDependencies.outputs.cosmosDBName
    projectPrincipalId: aiProject.outputs.projectPrincipalId
  }
}

module aiSearchRoleAssignments 'modules-standard/ai-search-role-assignments.bicep' = {
  name: 'ai-search-role-assignment'
  scope: rg
  params: {
    aiSearchName: aiDependencies.outputs.aiSearchName
    projectPrincipalId: aiProject.outputs.projectPrincipalId
  }
}

// Note: Capability hosts are commented out due to Bicep type definition issues
// They can be configured manually in the Azure Portal after deployment
// or added back when Bicep type definitions are updated

// Module to configure the Project Capability Host, linking everything together
// module addProjectCapabilityHost 'modules-standard/add-project-capability-host.bicep' = {
//   name: 'capabilityHost-configuration'
//   scope: rg
//   params: {
//     accountName: aiAccount.outputs.accountName
//     projectName: aiProject.outputs.projectName
//     cosmosDBConnection: aiProject.outputs.cosmosDBConnection
//     azureStorageConnection: aiProject.outputs.azureStorageConnection
//     aiSearchConnection: aiProject.outputs.aiSearchConnection
//     aoaiPassedIn: false
//     existingAoaiConnection: ''
//     projectCapHost: 'caphostproj'
//     accountCapHost: 'caphostacc'
//   }
//   dependsOn: [
//     aiSearchRoleAssignments
//     cosmosAccountRoleAssignments
//     storageAccountRoleAssignment
//   ]
// }

// NOTE: Container-level role assignments are commented out because the containers
// (enterprise_memory database and agent-specific containers) are created automatically
// by the Azure AI Agent Service when you first use it, not during infrastructure deployment.
// The account-level roles assigned above are sufficient for the service to function.
// These can be added later if needed after the containers exist.

// module storageContainersRoleAssignment 'modules-standard/blob-storage-container-role-assignments.bicep' = {
//   name: 'storage-containers-role-assignment'
//   scope: rg
//   params: {
//     aiProjectPrincipalId: aiProject.outputs.projectPrincipalId
//     storageName: aiDependencies.outputs.azureStorageName
//     workspaceId: formatProjectWorkspaceId.outputs.projectWorkspaceIdGuid
//   }
//   dependsOn: [
//     aiSearchRoleAssignments
//     cosmosAccountRoleAssignments
//     storageAccountRoleAssignment
//   ]
// }

// module cosmosContainerRoleAssignments 'modules-standard/cosmos-container-role-assignments.bicep' = {
//   name: 'cosmos-container-role-assignment'
//   scope: rg
//   params: {
//     cosmosAccountName: aiDependencies.outputs.cosmosDBName
//     projectWorkspaceId: formatProjectWorkspaceId.outputs.projectWorkspaceIdGuid
//     projectPrincipalId: aiProject.outputs.projectPrincipalId
//   }
//   dependsOn: [
//     aiSearchRoleAssignments
//     cosmosAccountRoleAssignments
//     storageAccountRoleAssignment
//   ]
// }

// =================================================================
// STEP 2: DEPLOY YOUR EXISTING APPLICATION INFRASTRUCTURE
// This section is mostly the same, but we will update it to use
// the new AI platform outputs.
// =================================================================

// User assigned managed identity for the function app (no change)
module apiUserAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: 'apiUserAssignedIdentity'
  scope: rg
  params: {
    location: location
    tags: tags
    name: !empty(apiUserAssignedIdentityName) ? apiUserAssignedIdentityName : '${abbrs.managedIdentityUserAssignedIdentities}api-${resourceToken}'
  }
}

module frontendUserAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: 'frontendUserAssignedIdentity'
  scope: rg
  params: {
    location: location
    tags: tags
    name: !empty(frontendUserAssignedIdentityName) ? frontendUserAssignedIdentityName : '${abbrs.managedIdentityUserAssignedIdentities}frontend-${resourceToken}'
  }
}

// Backing storage for Azure Functions api (no change)
module storage 'br/public:avm/res/storage/storage-account:0.8.3' = {
  name: 'storage'
  scope: rg
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
    skuName: 'Standard_LRS'
    blobServices: {
      containers: [
        { name: 'app-packages' }
        { name: 'snippets' }
      ]
    }
  }
}

// RBAC for your function app (no change)
var StorageBlobDataOwner = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
module blobRoleAssignmentApi 'app/rbac/storage-access.bicep' = {
  name: 'blobRoleAssignmentapi'
  scope: rg
  params: {
    storageAccountName: storage.outputs.name
    roleDefinitionID: StorageBlobDataOwner
    principalID: apiUserAssignedIdentity.outputs.principalId
  }
}

// Monitor application with Azure Monitor (no change)
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

// App Service Plan for Frontend (API uses its own Flex Consumption plan)
module frontendAppServicePlan 'br/public:avm/res/web/serverfarm:0.1.1' = {
  name: 'frontend-appserviceplan'
  scope: rg
  params: {
    name: '${abbrs.webServerFarms}frontend-${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      tier: 'Basic'
    }
    reserved: true
  }
}

// Durable Task Service (moved before API to resolve dependencies)
module dts './app/dts.bicep' = {
  scope: rg
  name: 'dtsResource'
  params: {
    name: !empty(dtsName) ? dtsName : '${abbrs.dts}${resourceToken}'
    taskhubname: !empty(taskHubName) ? taskHubName : '${abbrs.taskhub}${resourceToken}'
    location: location
    tags: tags
    ipAllowlist: [ '0.0.0.0/0' ]
    skuName: dtsSkuName
    skuCapacity: 1
  }
}

// Your application API - NOTE THE CHANGES TO appSettings
module api './app/api.bicep' = {
  name: 'api'
  scope: rg
  params: {
    name: !empty(apiServiceName) ? apiServiceName : '${abbrs.webSitesFunctions}api-${resourceToken}'
    location: location // You may want to use your region selector here
    tags: tags
    serviceName: 'backend' // azd service name
    resourceToken: resourceToken
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    storageAccountName: storage.outputs.name
    deploymentStorageContainerName: 'app-packages'
    identityId: apiUserAssignedIdentity.outputs.resourceId
    identityClientId: apiUserAssignedIdentity.outputs.clientId
    appSettings: {
      // --- UPDATED APP SETTINGS ---
      // Point to the new AI Project resources instead of the old ones.
      // Your application code will need to be updated to use the AI Agent SDK
      // to interact with the project.
      AZURE_AI_ACCOUNT_NAME: aiAccount.outputs.accountName
      AZURE_AI_PROJECT_NAME: aiProject.outputs.projectName
      AZURE_AI_PROJECT_ENDPOINT: aiAccount.outputs.accountTarget // The endpoint of the parent AI Account

      // --- OLD APP SETTINGS TO REMOVE OR UPDATE ---
      // COSMOS_ENDPOINT: cosmosDb.outputs.documentEndpoint // This is now managed by the AI project
      // EMBEDDING_MODEL_DEPLOYMENT_NAME: openai.outputs.embeddingDeploymentName // Models are managed by the project
      // AGENTS_MODEL_DEPLOYMENT_NAME: openai.outputs.chatDeploymentName
      // AZURE_OPENAI_ENDPOINT: openai.outputs.aiServicesEndpoint // Replaced by project info

      // --- Other settings ---
      DTS_CONNECTION_STRING: 'Endpoint=${dts.outputs.dts_URL};Authentication=ManagedIdentity;ClientID=${apiUserAssignedIdentity.outputs.clientId}'
      TASKHUBNAME: dts.outputs.TASKHUB_NAME
    }
  }
  dependsOn: [
    blobRoleAssignmentApi
    // You may need other dependsOn clauses here
  ]
}

// Frontend Web App
module frontend './app/frontend.bicep' = {
  name: 'frontend'
  scope: rg
  params: {
    name: !empty(frontendServiceName) ? frontendServiceName : '${abbrs.webSitesAppService}frontend-${resourceToken}'
    location: location
    tags: tags
    serviceName: 'frontend' // azd service name
    resourceToken: resourceToken
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    identityId: frontendUserAssignedIdentity.outputs.resourceId
    identityClientId: frontendUserAssignedIdentity.outputs.clientId
    appServicePlanId: frontendAppServicePlan.outputs.resourceId
    appSettings: {
      VITE_API_URL: 'https://${api.outputs.SERVICE_API_NAME}.azurewebsites.net'
    }
  }
}

// API Management service (no change)
module apim './app/apim.bicep' = {
  name: 'apim'
  scope: rg
  params: {
    name: !empty(apimServiceName) ? apimServiceName : '${abbrs.apiManagementService}${resourceToken}'
    location: location
    tags: tags
    publisherName: apimPublisherName
    publisherEmail: apimPublisherEmail
    appRegistrationClientId: appRegistrationClientId
  }
}


// ==================================
// Outputs
// ==================================
@description('The name of the new AI Account.')
output AZURE_AI_ACCOUNT_NAME string = aiAccount.outputs.accountName

@description('The name of the new AI Project.')
output AZURE_AI_PROJECT_NAME string = aiProject.outputs.projectName

@description('The endpoint for the new AI Account.')
output AZURE_AI_ENDPOINT string = aiAccount.outputs.accountTarget

@description('Name of the deployed Azure Function App.')
output AZURE_FUNCTION_NAME string = api.outputs.SERVICE_API_NAME

@description('Name of the deployed frontend web app.')
output AZURE_FRONTEND_NAME string = frontend.outputs.SERVICE_FRONTEND_NAME

@description('URL of the deployed frontend web app.')
output AZURE_FRONTEND_URI string = frontend.outputs.SERVICE_FRONTEND_URI

@description('API Management gateway URL for external API access.')
output APIM_GATEWAY_URL string = apim.outputs.gatewayUrl