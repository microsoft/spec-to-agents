@description('The name of the Azure AI Search service.')
param aiSearchName string

@description('The principal ID to assign the role to.')
param projectPrincipalId string

// Search Service Contributor role
var searchServiceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'

// Get the AI Search service resource
resource aiSearchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: aiSearchName
}

// Assign Search Service Contributor role to the project principal
resource searchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiSearchName, projectPrincipalId, searchServiceContributorRoleId)
  scope: aiSearchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchServiceContributorRoleId)
    principalId: projectPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = searchRoleAssignment.id
