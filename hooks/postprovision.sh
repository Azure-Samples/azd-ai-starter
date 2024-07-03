#!/bin/sh

if [ "$CREATE_IN_LOCAL" = "false" ]; then
    echo "Skipping postprovision.sh script execution as it is not in local."
else
    # Check if the Azure CLI is authenticated
    EXPIRED_TOKEN=$(az ad signed-in-user show --query 'id' -o tsv 2>/dev/null || true)

    if [ -z "$EXPIRED_TOKEN" ]; then
        echo "No Azure user signed in. Please login."
        az login -o none
    fi

    az account set -s $AZURE_SUBSCRIPTION_ID

    apiKey=$(az cognitiveservices account keys list --name $AZURE_OPENAI_NAME --resource-group $AZURE_RESOURCE_GROUP --query key1 --output tsv)
    azd env set AZURE_OPENAI_KEY $apiKey

    echo "An Azure OpenAI API key has been added to your azd environment variable named 'AZURE_OPENAI_KEY' that can be used for testing"
    echo ""
    echo "======================================================================================================"
    echo "IMPORTANT! - Do not commit this key to your repository or share it with others."
    echo "Instead use a secure solution like Azure Key Vault or leverage managed identities for Azure resources."
    echo "======================================================================================================"
    echo ""
fi