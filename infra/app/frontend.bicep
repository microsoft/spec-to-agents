param name string
param location string = resourceGroup().location
param tags object = {}
param applicationInsightsName string = ''
param appSettings object = {}
param serviceName string = 'frontend'
param identityId string = ''
param identityClientId string = ''
param resourceToken string = ''
param appServicePlanId string

@allowed(['SystemAssigned', 'UserAssigned'])
param identityType string = 'UserAssigned'

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

var applicationInsightsIdentity = 'ClientId=${identityClientId};Authorization=AAD'

// Frontend Web App
module frontend 'br/public:avm/res/web/site:0.15.1' = {
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
    serverFarmResourceId: appServicePlanId
    siteConfig: {
      linuxFxVersion: 'NODE|20-lts'
      alwaysOn: true
      appCommandLine: 'pm2 serve /home/site/wwwroot --no-daemon --spa'
    }
    appSettingsKeyValuePairs: union(appSettings, {
      APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
      APPLICATIONINSIGHTS_AUTHENTICATION_STRING: applicationInsightsIdentity
    })
  }
}

output SERVICE_FRONTEND_NAME string = frontend.outputs.name
output SERVICE_FRONTEND_URI string = 'https://${frontend.outputs.defaultHostname}'
output SERVICE_FRONTEND_IDENTITY_PRINCIPAL_ID string = identityType == 'SystemAssigned' ? frontend.outputs.?systemAssignedMIPrincipalId ?? '' : ''

