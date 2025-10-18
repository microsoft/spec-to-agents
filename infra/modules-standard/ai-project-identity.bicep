@description('The name of the Azure AI Account.')
param accountName string

@description('The name of the AI Project.')
param projectName string

@description('The description of the AI Project.')
param projectDescription string

@description('The display name of the AI Project.')
param displayName string

@description('The location where the AI Project will be created.')
param location string

@description('The tags to apply to the AI Project.')
param tags object = {}

@description('The name of the Azure AI Search service.')
param aiSearchName string

@description('The resource group name of the AI Search service.')
param aiSearchServiceResourceGroupName string

@description('The subscription ID of the AI Search service.')
param aiSearchServiceSubscriptionId string

@description('The name of the Cosmos DB account.')
param cosmosDBName string

@description('The subscription ID of the Cosmos DB account.')
param cosmosDBSubscriptionId string

@description('The resource group name of the Cosmos DB account.')
param cosmosDBResourceGroupName string

@description('The name of the Azure Storage account.')
param azureStorageName string

@description('The subscription ID of the Azure Storage account.')
param azureStorageSubscriptionId string

@description('The resource group name of the Azure Storage account.')
param azureStorageResourceGroupName string

@description('Whether an existing Azure OpenAI resource is being used.')
param aoaiPassedIn bool = false

@description('The name of the existing Azure OpenAI resource.')
param existingAoaiName string = ''

@description('The subscription ID of the existing Azure OpenAI resource.')
param existingAoaiSubscriptionId string = ''

@description('The resource group name of the existing Azure OpenAI resource.')
param existingAoaiResourceGroupName string = ''

// Create the AI Project
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: projectName
  location: location
  tags: tags
  kind: 'Project'
  properties: {
    description: projectDescription
    friendlyName: displayName
    keyVault: ''
    storageAccount: ''
    applicationInsights: ''
    containerRegistry: ''
    hbiWorkspace: false
    allowPublicAccessWhenBehindVnet: false
    imageBuildCompute: ''
    primaryUserAssignedIdentity: ''
    managedNetwork: {
      isolationMode: 'Disabled'
    }
    hubResourceId: resourceId('Microsoft.MachineLearningServices/workspaces', accountName)
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Create connections to dependencies
resource aiSearchConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
  parent: aiProject
  name: 'ai-search-connection'
  properties: {
    category: 'AzureCognitiveSearch'
    target: resourceId(aiSearchServiceSubscriptionId, aiSearchServiceResourceGroupName, 'Microsoft.Search/searchServices', aiSearchName)
    authType: 'ManagedIdentity'
  }
}

resource cosmosConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
  parent: aiProject
  name: 'cosmos-connection'
  properties: {
    category: 'AzureCosmosDb'
    target: resourceId(cosmosDBSubscriptionId, cosmosDBResourceGroupName, 'Microsoft.DocumentDB/databaseAccounts', cosmosDBName)
    authType: 'ManagedIdentity'
  }
}

resource storageConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
  parent: aiProject
  name: 'storage-connection'
  properties: {
    category: 'AzureBlob'
    target: resourceId(azureStorageSubscriptionId, azureStorageResourceGroupName, 'Microsoft.Storage/storageAccounts', azureStorageName)
    authType: 'ManagedIdentity'
  }
}

resource openaiConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = if (aoaiPassedIn) {
  parent: aiProject
  name: 'openai-connection'
  properties: {
    category: 'AzureOpenAI'
    target: resourceId(existingAoaiSubscriptionId, existingAoaiResourceGroupName, 'Microsoft.CognitiveServices/accounts', existingAoaiName)
    authType: 'ManagedIdentity'
  }
}

output projectName string = aiProject.name
output projectId string = aiProject.id
output projectWorkspaceId string = aiProject.properties.workspaceId
output projectPrincipalId string = aiProject.identity.principalId
output aiSearchConnection string = aiSearchConnection.id
output cosmosDBConnection string = cosmosConnection.id
output azureStorageConnection string = storageConnection.id
