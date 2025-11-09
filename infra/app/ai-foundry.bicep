param location string = resourceGroup().location
param tags object = {}
param accountName string
param projectName string
param projectDescription string = 'AI Agents Project'
param projectDisplayName string

// Model deployment parameters
param modelName string = 'gpt-5-mini'
param modelFormat string = 'OpenAI'
param modelVersion string = '2025-08-07'
param modelSkuName string = 'GlobalStandard'
param modelCapacity int = 100

// Second model deployment parameters (for web search)
param webSearchModelName string = 'gpt-4.1-mini'
param webSearchModelVersion string = '2025-04-14'
param webSearchModelCapacity int = 1000  // 1M TPM (1000 units = 1,000,000 tokens per minute)

// Bing grounding parameters
param bingAccountName string

// Deploy Bing Grounding resource
#disable-next-line BCP081
resource bingAccount 'Microsoft.Bing/accounts@2025-05-01-preview' = {
  name: bingAccountName
  location: 'global'
  kind: 'Bing.Grounding'
  sku: {
    name: 'G1'
  }
}

// Deploy AI Services Account (AI Foundry Hub)
#disable-next-line BCP081
resource account 'Microsoft.CognitiveServices/accounts@2025-09-01' = {
  name: accountName
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: toLower(accountName)
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false  // Enable API key authentication for inference
  }
}

// Deploy Project under AI Services Account
#disable-next-line BCP081
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-09-01' = {
  parent: account
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: projectDescription
    displayName: projectDisplayName
  }

  // Create project connection to Bing grounding
  resource bingGroundingConnection 'connections' = {
    name: replace(bingAccountName, '-', '')
    properties: {
      authType: 'ApiKey'
      target: bingAccount.properties.endpoint
      category: 'GroundingWithBingSearch'
      metadata: {
        type: 'bing_grounding'
        ApiType: 'Azure'
        ResourceId: bingAccount.id
        location: bingAccount.location
      }
      credentials: {
        key: bingAccount.listKeys().key1
      }
      isSharedToAll: false
    }
  }
}

// Deploy primary model (gpt-5-mini by default)
#disable-next-line BCP081
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-09-01' = {
  parent: account
  name: modelName
  sku: {
    capacity: modelCapacity
    name: modelSkuName
  }
  properties: {
    model: {
      name: modelName
      format: modelFormat
      version: modelVersion
    }
  }
}

// Deploy web search model (gpt-4.1-mini by default)
#disable-next-line BCP081
resource webSearchModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-09-01' = {
  parent: account
  name: webSearchModelName
  sku: {
    capacity: webSearchModelCapacity
    name: modelSkuName
  }
  properties: {
    model: {
      name: webSearchModelName
      format: modelFormat
      version: webSearchModelVersion
    }
  }
  dependsOn: [
    modelDeployment  // Ensure sequential deployment
  ]
}

output accountName string = account.name
output projectName string = project.name
output accountEndpoint string = account.properties.endpoint
output accountId string = account.id
output projectId string = project.id
output modelDeploymentName string = modelDeployment.name
output webSearchModelDeploymentName string = webSearchModelDeployment.name
output bingConnectionName string = project::bingGroundingConnection.name
output bingConnectionId string = '${project.id}/connections/${project::bingGroundingConnection.name}'
output bingAccountName string = bingAccount.name
