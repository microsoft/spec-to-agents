@description('The name of the Cosmos DB account.')
param cosmosDBName string

@description('The principal ID to assign the role to.')
param projectPrincipalId string

// Cosmos DB Built-in Data Contributor role
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

// Get the Cosmos DB account resource
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-09-15' existing = {
  name: cosmosDBName
}

// Assign Cosmos DB Built-in Data Contributor role to the project principal
resource cosmosRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosDBName, projectPrincipalId, cosmosDataContributorRoleId)
  scope: cosmosAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cosmosDataContributorRoleId)
    principalId: projectPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = cosmosRoleAssignment.id
