@description('The name of the Azure AI Account.')
param accountName string

@description('The location where the Azure AI Account will be created.')
param location string

@description('The tags to apply to the Azure AI Account.')
param tags object = {}

// Create the Azure AI Account
resource aiAccount 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'AIServices'
  properties: {
    description: 'Azure AI Account for AI Agent Service'
    friendlyName: accountName
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
  }
  identity: {
    type: 'SystemAssigned'
  }
}

output accountName string = aiAccount.name
output accountId string = aiAccount.id
output accountTarget string = aiAccount.properties.discoveryUrl
output accountPrincipalId string = aiAccount.identity.principalId
