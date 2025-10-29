/*
This module creates a Grounding with Bing Search resource and establishes
a connection from your AI Foundry account to enable real-time web search
capabilities for agents.

Learn more:
- https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding
- https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-code-samples
*/

@description('Name of the AI Foundry account to connect to')
param aiFoundryAccountName string

@description('Name for the Bing Grounding resource')
param bingResourceName string

@description('Location for the Bing Grounding resource. Bing resources are typically deployed to "global".')
param location string = 'global'

@description('Tags to apply to the Bing resource')
param tags object = {}

@description('Whether to create a new Bing resource or use an existing one')
@allowed([
  'new'
  'existing'
])
param newOrExisting string = 'new'

// Reference to the existing AI Foundry account
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiFoundryAccountName
}

// Conditionally reference an existing Bing Grounding resource
resource existingBingGrounding 'Microsoft.Bing/accounts@2020-06-10' existing = if (newOrExisting == 'existing') {
  name: bingResourceName
}

// Conditionally create a new Bing Grounding resource
resource newBingGrounding 'Microsoft.Bing/accounts@2020-06-10' = if (newOrExisting == 'new') {
  name: bingResourceName
  location: location
  tags: tags
  sku: {
    name: 'G1' // Grounding with Bing Search SKU
  }
  kind: 'Bing.Grounding'
  properties: {
    statisticsEnabled: false
  }
}

// Create the connection from AI Foundry to Bing Grounding
// Note: The connection uses the Bing resource's API key for authentication
resource bingConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  name: 'bing-grounding'
  parent: aiFoundry
  properties: {
    category: 'ApiKey'
    target: 'https://api.bing.microsoft.com/'
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: (newOrExisting == 'new') ? newBingGrounding.listKeys().key1 : existingBingGrounding.listKeys().key1
    }
    metadata: {
      ApiType: 'Azure'
      Type: 'bing_grounding'
      ResourceId: (newOrExisting == 'new') ? newBingGrounding.id : existingBingGrounding.id
    }
  }
}

// Outputs
@description('The resource ID of the Bing Grounding resource')
output bingResourceId string = (newOrExisting == 'new') ? newBingGrounding.id : existingBingGrounding.id

@description('The name of the Bing Grounding resource')
output bingResourceName string = (newOrExisting == 'new') ? newBingGrounding.name : existingBingGrounding.name

@description('The connection name for Bing Grounding')
output bingConnectionName string = bingConnection.name

@description('The connection ID for use in agent configuration')
output bingConnectionId string = bingConnection.id

