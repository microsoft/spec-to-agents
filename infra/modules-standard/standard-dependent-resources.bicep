@description('The location where resources will be created.')
param location string

@description('The name of the Azure Storage account.')
param azureStorageName string

@description('The name of the Azure AI Search service.')
param aiSearchName string

@description('The name of the Cosmos DB account.')
param cosmosDBName string

@description('Whether the Azure Storage account already exists.')
param azureStorageExists bool = false

@description('Whether the Azure AI Search service already exists.')
param aiSearchExists bool = false

@description('Whether the Cosmos DB account already exists.')
param cosmosDBExists bool = false

@description('The resource ID of the existing Azure Storage account.')
param azureStorageAccountResourceId string = ''

@description('The resource ID of the existing Azure AI Search service.')
param aiSearchResourceId string = ''

@description('The resource ID of the existing Cosmos DB account.')
param cosmosDBResourceId string = ''

@description('The tags to apply to resources.')
param tags object = {}

var cosmosParts = split(cosmosDBResourceId, '/')

var canaryRegions = ['eastus2euap', 'centraluseuap']
var cosmosDbRegion = contains(canaryRegions, location) ? 'westus' : location

var acsParts = split(aiSearchResourceId, '/')

var azureStorageParts = split(azureStorageAccountResourceId, '/')

resource existingCosmosDB 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = if (cosmosDBExists) {
  name: cosmosParts[8]
  scope: resourceGroup(cosmosParts[2], cosmosParts[4])
}

resource existingSearchService 'Microsoft.Search/searchServices@2024-06-01-preview' existing = if (aiSearchExists) {
  name: acsParts[8]
  scope: resourceGroup(acsParts[2], acsParts[4])
}

resource existingAzureStorageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = if (azureStorageExists) {
  name: azureStorageParts[8]
  scope: resourceGroup(azureStorageParts[2], azureStorageParts[4])
}

// Some regions doesn't support Standard Zone-Redundant storage, need to use Geo-redundant storage
param noZRSRegions array = ['southindia', 'westus']
param sku object = contains(noZRSRegions, location) ? { name: 'Standard_GRS' } : { name: 'Standard_ZRS' }

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = if(!azureStorageExists) {
  name: azureStorageName
  location: location
  kind: 'StorageV2'
  sku: sku
  tags: tags
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
      virtualNetworkRules: []
    }
    allowSharedKeyAccess: false
  }
}

// Create Azure AI Search service if it doesn't exist
resource aiSearch 'Microsoft.Search/searchServices@2024-06-01-preview' = if(!aiSearchExists) {
  name: aiSearchName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    disableLocalAuth: false
    authOptions: { aadOrApiKey: { aadAuthFailureMode: 'http401WithBearerChallenge'}}
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    hostingMode: 'default'
    partitionCount: 1
    publicNetworkAccess: 'enabled'
    replicaCount: 1
    semanticSearch: 'disabled'
  }
  sku: {
    name: 'standard'
  }
}

// Create Cosmos DB account if it doesn't exist
resource cosmosDB 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = if(!cosmosDBExists) {
  name: cosmosDBName
  location: cosmosDbRegion
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    disableLocalAuth: true
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    enableFreeTier: false
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
  }
}

// Create Cosmos DB database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-09-15' = if (!cosmosDBExists) {
  parent: cosmosDB
  name: 'ai-agent-db'
  properties: {
    resource: {
      id: 'ai-agent-db'
    }
  }
}

// Create Cosmos DB container
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-09-15' = if (!cosmosDBExists) {
  parent: cosmosDatabase
  name: 'ai-agent-container'
  properties: {
    resource: {
      id: 'ai-agent-container'
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

output aiSearchName string = aiSearchExists ? existingSearchService.name : aiSearch.name
output aiSearchID string = aiSearchExists ? existingSearchService.id : aiSearch.id
output aiSearchServiceResourceGroupName string = aiSearchExists ? acsParts[4] : resourceGroup().name
output aiSearchServiceSubscriptionId string = aiSearchExists ? acsParts[2] : subscription().subscriptionId

output azureStorageName string = azureStorageExists ? existingAzureStorageAccount.name : storage.name
output azureStorageId string = azureStorageExists ? existingAzureStorageAccount.id : storage.id
output azureStorageResourceGroupName string = azureStorageExists ? azureStorageParts[4] : resourceGroup().name
output azureStorageSubscriptionId string = azureStorageExists ? azureStorageParts[2] : subscription().subscriptionId

output cosmosDBName string = cosmosDBExists ? existingCosmosDB.name : cosmosDB.name
output cosmosDBId string = cosmosDBExists ? existingCosmosDB.id : cosmosDB.id
output cosmosDBResourceGroupName string = cosmosDBExists ? cosmosParts[4] : resourceGroup().name
output cosmosDBSubscriptionId string = cosmosDBExists ? cosmosParts[2] : subscription().subscriptionId
