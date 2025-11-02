param aiAccountName string
param roleDefinitionID string
param principalID string
param principalType string = 'ServicePrincipal'

resource aiAccount 'Microsoft.CognitiveServices/accounts@2025-09-01' existing = {
  name: aiAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: aiAccount
  name: guid(aiAccount.id, principalID, roleDefinitionID)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionID)
    principalId: principalID
    principalType: principalType
  }
}

output roleAssignmentId string = roleAssignment.id
