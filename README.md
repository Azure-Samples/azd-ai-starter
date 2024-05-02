---
page_type: sample
languages:
- azdeveloper
- bicep
products:
- azure
urlFragment: azd-ai-starter
name: Azure AI starter template
description: Creates an Azure AI Service and deploys the specified models.
---
<!-- YAML front-matter schema: https://review.learn.microsoft.com/en-us/help/contribute/samples/process/onboarding?branch=main#supported-metadata-fields-for-readmemd -->

# Azure AI Starter Template

### Quickstart
To learn how to get started with any template, follow the steps in [this quickstart](https://learn.microsoft.com/azure/developer/azure-developer-cli/get-started?tabs=localinstall&pivots=programming-language-nodejs) with this template(`wbreza/azd-ai-starter`)

This quickstart will show you how to authenticate on Azure, initialize using a template, provision infrastructure and deploy code on Azure via the following commands:

```bash
# Log in to azd. Only required once per-install.
azd auth login

# First-time project setup. Initialize a project in the current directory, using this template. 
azd init --template wbreza/azd-ai-starter

# Provision and deploy to Azure
azd up
```

### Provisioned Azure Resources

This template creates the following resources:

- [OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)

The provisioning will also deploy any models specified within the `./infra/ai.yaml`.

For a list of supported models see [Azure OpenAI Service Models documentation](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)

### Optional Configuration

By default this template will use a default naming convention to prevent naming collisions within Azure.
To override default naming conventions the following can be set.

- `AZURE_OPENAI_NAME` - The name of the Azure Open AI service

Run `azd config set <key> <value>` after initializing the template to override the resource names

## Reporting Issues and Feedback

If you have any feature requests, issues, or areas for improvement, please [file an issue](https://aka.ms/azure-dev/issues). To keep up-to-date, ask questions, or share suggestions, join our [GitHub Discussions](https://aka.ms/azure-dev/discussions). You may also contact us via AzDevTeam@microsoft.com.
