@description('The name of the Azure AI Account.')
param accountName string

@description('The name of the AI Project.')
param projectName string

@description('The Cosmos DB connection ID.')
param cosmosDBConnection string

@description('The Azure Storage connection ID.')
param azureStorageConnection string

@description('The AI Search connection ID.')
param aiSearchConnection string

@description('Whether an existing Azure OpenAI resource is being used.')
param aoaiPassedIn bool = false

@description('The existing Azure OpenAI connection ID.')
param existingAoaiConnection string = ''

@description('The project capability host name.')
param projectCapHost string

@description('The account capability host name.')
param accountCapHost string

// Get the AI Project resource
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: projectName
}

// Get the AI Account resource
resource aiAccount 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: accountName
}

// Create project capability host
resource projectCapabilityHost 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = {
  parent: aiProject
  name: projectCapHost
  properties: {
    computeType: 'AIServices' // @suppress BCP036 - AIServices is valid but not in Bicep type definitions yet
    properties: {
      aiServicesResourceId: aiAccount.id
      connections: union([
        {
          connectionId: cosmosDBConnection
          connectionType: 'AzureCosmosDb'
        }
        {
          connectionId: azureStorageConnection
          connectionType: 'AzureBlob'
        }
        {
          connectionId: aiSearchConnection
          connectionType: 'AzureCognitiveSearch'
        }
      ], aoaiPassedIn ? [
        {
          connectionId: existingAoaiConnection
          connectionType: 'AzureOpenAI'
        }
      ] : [])
    }
  }
}

// Create account capability host
resource accountCapabilityHost 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = {
  parent: aiAccount
  name: accountCapHost
  properties: {
    computeType: 'AIServices' // @suppress BCP036 - AIServices is valid but not in Bicep type definitions yet
    properties: {
      aiServicesResourceId: aiAccount.id
      connections: []
    }
  }
}

output projectCapabilityHostId string = projectCapabilityHost.id
output accountCapabilityHostId string = accountCapabilityHost.id
