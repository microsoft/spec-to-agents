@description('The principal ID of the AI Project.')
param aiProjectPrincipalId string

@description('The name of the storage account.')
param storageName string

@description('The workspace ID of the AI Project.')
param workspaceId string

// Storage Blob Data Owner role
var storageBlobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'

// Get the storage account resource
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageName
}

// Get the blob service
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' existing = {
  parent: storageAccount
  name: 'default'
}

// Create containers for the AI Project
resource aiProjectContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'ai-project-${workspaceId}'
  properties: {
    publicAccess: 'None'
    metadata: {
      'ai-project': 'true'
    }
  }
}

// Assign Storage Blob Data Owner role to the project principal
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageName, aiProjectPrincipalId, storageBlobDataOwnerRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataOwnerRoleId)
    principalId: aiProjectPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output containerName string = aiProjectContainer.name
output roleAssignmentId string = storageRoleAssignment.id
