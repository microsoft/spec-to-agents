param name string
param location string = resourceGroup().location
param tags object = {}
param applicationInsightsName string = ''
param appSettings object = {}
param serviceName string = 'app'
param virtualNetworkSubnetId string = ''
param identityId string = ''
param identityClientId string = ''
param resourceToken string

param runtimeVersion string = '3.11'

@allowed(['SystemAssigned', 'UserAssigned'])
param identityType string = 'UserAssigned'

var abbrs = loadJsonContent('../abbreviations.json')

var applicationInsightsIdentity = 'ClientId=${identityClientId};Authorization=AAD'

// Use a standard App Service plan instead of Flex Consumption
// Use a different name suffix (-web) to avoid conflict with existing FlexConsumption plan
module appServicePlan 'br/public:avm/res/web/serverfarm:0.1.1' = {
  name: 'appserviceplan'
  params: {
    name: '${abbrs.webServerFarms}web-${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      tier: 'Basic'
    }
    reserved: true
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

// Deploy as a standard web app, not a function app
module app 'br/public:avm/res/web/site:0.15.1' = {
  name: '${serviceName}-webapp-module'
  params: {
    name: name
    location: location
    kind: 'app,linux'
    tags: union(tags, { 'azd-service-name': serviceName })
    managedIdentities: {
      systemAssigned: identityType == 'SystemAssigned'
      userAssignedResourceIds: identityType == 'UserAssigned' ? [identityId] : []
    }
    serverFarmResourceId: appServicePlan.outputs.resourceId
    siteConfig: {
      linuxFxVersion: 'PYTHON|${runtimeVersion}'
      alwaysOn: true
      appCommandLine: 'python -m spec_to_agents.main'
    }
    appSettingsKeyValuePairs: union(appSettings, {
      SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
      APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
      APPLICATIONINSIGHTS_AUTHENTICATION_STRING: applicationInsightsIdentity
    })
    virtualNetworkSubnetId: !empty(virtualNetworkSubnetId) ? virtualNetworkSubnetId : null
  }
}

output SERVICE_APP_NAME string = app.outputs.name
output SERVICE_APP_URI string = 'https://${app.outputs.defaultHostname}'
output SERVICE_APP_IDENTITY_PRINCIPAL_ID string = identityType == 'SystemAssigned' ? app.outputs.?systemAssignedMIPrincipalId ?? '' : ''
