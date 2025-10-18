@description('The name of the Cosmos DB account.')
param cosmosAccountName string

@description('The workspace ID of the AI Project.')
param projectWorkspaceId string

@description('The principal ID of the AI Project.')
param projectPrincipalId string

// Cosmos DB Built-in Data Contributor role
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

// Get the Cosmos DB account resource
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-09-15' existing = {
  name: cosmosAccountName
}

// Create database for the AI Project
resource aiProjectDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-09-15' = {
  parent: cosmosAccount
  name: 'ai-project-${projectWorkspaceId}'
  properties: {
    resource: {
      id: 'ai-project-${projectWorkspaceId}'
    }
  }
}

// Create container for the AI Project
resource aiProjectContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-09-15' = {
  parent: aiProjectDatabase
  name: 'ai-agent-data'
  properties: {
    resource: {
      id: 'ai-agent-data'
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
      }
      defaultTtl: -1
      uniqueKeyPolicy: {
        uniqueKeys: []
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
    }
  }
}

// Assign Cosmos DB Built-in Data Contributor role to the project principal
resource cosmosRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosAccountName, projectPrincipalId, cosmosDataContributorRoleId)
  scope: cosmosAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cosmosDataContributorRoleId)
    principalId: projectPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output databaseName string = aiProjectDatabase.name
output containerName string = aiProjectContainer.name
output roleAssignmentId string = cosmosRoleAssignment.id
