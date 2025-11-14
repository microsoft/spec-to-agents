param name string
param location string = resourceGroup().location
param tags object = {}
param applicationInsightsName string = ''
param appSettings array = []
param serviceName string = 'app'
param identityId string = ''
param resourceToken string
param containerRegistryName string

@allowed(['SystemAssigned', 'UserAssigned', 'SystemAssigned,UserAssigned'])
param identityType string = 'UserAssigned'

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

// Create Container Apps Environment
module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.8.2' = {
  name: 'container-apps-environment'
  params: {
    name: 'cae-${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceResourceId: applicationInsights.properties.WorkspaceResourceId
    zoneRedundant: false  // Disable zone redundancy since we're not using VNet
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// Deploy Container App
module containerApp 'br/public:avm/res/app/container-app:0.11.0' = {
  name: '${serviceName}-container-app'
  params: {
    name: name
    location: location
    tags: union(tags, { 'azd-service-name': serviceName })
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      systemAssigned: contains(identityType, 'SystemAssigned')
      userAssignedResourceIds: contains(identityType, 'UserAssigned') ? [identityId] : []
    }
    registries: [
      {
        server: containerRegistry.properties.loginServer
        identity: contains(identityType, 'UserAssigned') ? identityId : ''
      }
    ]
    containers: [
      {
        name: 'main'
        // Use a placeholder image during initial provisioning, azd will update this during deployment
        image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
        resources: {
          cpu: json('0.5')
          memory: '1Gi'
        }
        env: appSettings
      }
    ]
    ingressTargetPort: 8080
    ingressExternal: true
    ingressTransport: 'auto'
    scaleMinReplicas: 1
    scaleMaxReplicas: 3
  }
}

output SERVICE_APP_NAME string = containerApp.outputs.name
output SERVICE_APP_URI string = containerApp.outputs.fqdn
output SERVICE_APP_IDENTITY_PRINCIPAL_ID string = contains(identityType, 'SystemAssigned') ? containerApp.outputs.systemAssignedMIPrincipalId : ''
output environmentId string = containerAppsEnvironment.outputs.resourceId
