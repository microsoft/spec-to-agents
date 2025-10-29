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

// Validate that if exists flags are true, resource IDs are provided
@assert(azureStorageExists == false || !empty(azureStorageAccountResourceId), 'Azure Storage account resource ID must be provided when azureStorageExists is true')
@assert(aiSearchExists == false || !empty(aiSearchResourceId), 'Azure AI Search resource ID must be provided when aiSearchExists is true')
@assert(cosmosDBExists == false || !empty(cosmosDBResourceId), 'Cosmos DB resource ID must be provided when cosmosDBExists is true')

output azureStorageExists bool = azureStorageExists
output aiSearchExists bool = aiSearchExists
output cosmosDBExists bool = cosmosDBExists
