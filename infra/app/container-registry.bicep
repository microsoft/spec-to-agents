param name string
param location string = resourceGroup().location
param tags object = {}

@description('SKU for the container registry')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

@description('Enable admin user')
param adminUserEnabled bool = true

// Deploy Azure Container Registry
module containerRegistry 'br/public:avm/res/container-registry/registry:0.5.1' = {
  name: 'container-registry'
  params: {
    name: name
    location: location
    tags: tags
    acrSku: sku
    acrAdminUserEnabled: adminUserEnabled
  }
}

output name string = containerRegistry.outputs.name
output loginServer string = containerRegistry.outputs.loginServer
output resourceId string = containerRegistry.outputs.resourceId
