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

// Create Azure Storage Account if it doesn't exist
resource azureStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = if (!azureStorageExists) {
  name: azureStorageName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// Create Azure AI Search service if it doesn't exist
resource aiSearch 'Microsoft.Search/searchServices@2023-11-01' = if (!aiSearchExists) {
  name: aiSearchName
  location: location
  tags: tags
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      ipRules: []
    }
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    disableLocalAuth: false
    authOptions: {
      apiKeyOnly: {}
    }
    semanticSearch: 'disabled'
  }
}

// Create Cosmos DB account if it doesn't exist
resource cosmosDB 'Microsoft.DocumentDB/databaseAccounts@2023-09-15' = if (!cosmosDBExists) {
  name: cosmosDBName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    isVirtualNetworkFilterEnabled: false
    virtualNetworkRules: []
    enableCassandraConnector: false
    disableKeyBasedMetadataWriteAccess: false
    keyVaultKeyUri: ''
    enableFreeTier: false
    apiProperties: {
      serverVersion: '3.2'
    }
    enableAnalyticalStorage: false
    analyticalStorageConfiguration: {
      schemaType: 'WellDefined'
    }
    createMode: 'Default'
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'Geo'
      }
    }
    cors: []
    capabilities: []
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

output azureStorageName string = azureStorageExists ? last(split(azureStorageAccountResourceId, '/')) : azureStorage.name
output azureStorageId string = azureStorageExists ? azureStorageAccountResourceId : azureStorage.id
output aiSearchName string = aiSearchExists ? last(split(aiSearchResourceId, '/')) : aiSearch.name
output aiSearchId string = aiSearchExists ? aiSearchResourceId : aiSearch.id
output cosmosDBName string = cosmosDBExists ? last(split(cosmosDBResourceId, '/')) : cosmosDB.name
output cosmosDBId string = cosmosDBExists ? cosmosDBResourceId : cosmosDB.id
