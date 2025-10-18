param logAnalyticsName string
param applicationInsightsName string
param location string = resourceGroup().location
param tags object = {}
param disableLocalAuth bool = false

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.7.0' = {
  name: 'loganalytics'
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
  }
}

module applicationInsights 'br/public:avm/res/insights/component:0.4.1'  = {
  name: 'applicationinsights'
  params: {
    name: applicationInsightsName
    location: location
    tags: tags
    workspaceResourceId: logAnalytics.outputs.resourceId
    disableLocalAuth: disableLocalAuth
  }
}

output applicationInsightsConnectionString string = applicationInsights.outputs.connectionString
output applicationInsightsInstrumentationKey string = applicationInsights.outputs.instrumentationKey
output applicationInsightsName string = applicationInsights.outputs.name
output logAnalyticsWorkspaceId string = logAnalytics.outputs.resourceId
output logAnalyticsWorkspaceName string = logAnalytics.outputs.name
