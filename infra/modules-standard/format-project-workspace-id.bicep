@description('The project workspace ID.')
param projectWorkspaceId string

// Convert workspace ID to GUID format
var workspaceIdGuid = projectWorkspaceId

output projectWorkspaceIdGuid string = workspaceIdGuid
