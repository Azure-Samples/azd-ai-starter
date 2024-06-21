if ($env:CREATE_IN_LOCAL -eq "false") {
    Write-Host "Skipping postprovision script for non local."
}
else {
    # Check if the Azure CLI is authenticated
    $EXPIRED_TOKEN = (az ad signed-in-user show --query 'id' -o tsv 2>$null)

    if (-not $EXPIRED_TOKEN) {
        Write-Host "No Azure user signed in. Please login."
        az login -o none
    }

    az account set -s $env:AZURE_SUBSCRIPTION_ID

    $apiKey = (az cognitiveservices account keys list --name $env:AZURE_OPENAI_NAME --resource-group $env:AZURE_RESOURCE_GROUP --query key1 --output tsv)
    azd env set AZURE_OPENAI_KEY $apiKey

    Write-Host "An Azure OpenAI API key has been added to your azd environment variable named 'AZURE_OPENAI_KEY' that can be used for testing"
    Write-Host ""
    Write-Host "======================================================================================================"
    Write-Host "IMPORTANT! - Do not commit this key to your repository or share it with others."
    Write-Host "Instead use a secure solution like Azure Key Vault or leverage managed identities for Azure resources."
    Write-Host "======================================================================================================"
    Write-Host ""
}