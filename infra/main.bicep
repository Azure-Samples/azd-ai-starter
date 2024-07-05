targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('The Azure resource group where new resources will be deployed')
param resourceGroupName string = ''
@description('The Open AI resource name. If ommited will be generated')
param openAiName string = ''

param createRoleForUser bool = true

var aiConfig = loadYamlContent('./ai.yaml')

param principalId string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

module cognitiveServices 'core/ai/cognitiveservices.bicep' = {
  name: 'cognitiveServices'
  scope: rg
  params: {
    location: location
    tags: tags
    name: !empty(openAiName) ? openAiName : 'aoai-${resourceToken}'
    kind: 'AIServices'
    deployments: contains(aiConfig, 'deployments') ? aiConfig.deployments : []
  }
}

module userRoleDataScientist 'core/security/role.bicep' =  if (createRoleForUser) {
  name: 'user-role-data-scientist'
  scope: rg
  params: {
    principalId: principalId
    roleDefinitionId: 'f6c7c914-8db3-469d-8ca1-694a8f32e121'
    principalType: 'User'
  }
}

// output the names of the resources
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

output AZURE_OPENAI_NAME string = cognitiveServices.outputs.name
output AZURE_OPENAI_ENDPOINT string = cognitiveServices.outputs.endpoints['OpenAI Language Model Instance API']
