@description('The name of the Azure Storage account.')
param azureStorageName string

@description('The principal ID to assign the role to.')
param projectPrincipalId string

// Storage Blob Data Owner role
var storageBlobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'

// Get the storage account resource
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: azureStorageName
}

// Assign Storage Blob Data Owner role to the project principal
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(azureStorageName, projectPrincipalId, storageBlobDataOwnerRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataOwnerRoleId)
    principalId: projectPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = storageRoleAssignment.id
