<#
.SYNOPSIS
    This script uses Azure CLI to list the remaining quotas for the specified models in the specified locations.
.DESCRIPTION
    This script lists the remaining quotas for the specified models in the specified locations.
    The script requires Azure CLI to be installed and logged in.
.EXAMPLE
    az login
    ./listAIQuotas.ps1
.EXAMPLE
    ./listAIQuotas.ps1 -s <subscription_id>
.EXAMPLE
    ./listAIQuotas.ps1 -m "OpenAI.Standard.gpt-35-turbo:1106,0301,0613 OpenAI.Standard.gpt-4:1106-Preview"
.EXAMPLE
    ./listAIQuotas.ps1 -m "OpenAI.Standard.gpt-35-turbo OpenAI.Standard.gpt-4:*"
.PARAMETER subscription
    The subscription ID to fetch the quotas from. If not provided, the script will use the current subscription.
.PARAMETER models
    The list of candidate models to fetch the quotas for. The format is "kind.sku.name:version1,version2 kind.sku.name:version1,version2".
    If not provided, the script will use the default candidate models.
.PARAMETER help
    Show the help message.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [Alias("s")]
    [string] $subscription,
    [Parameter(Mandatory = $false)]
    [Alias("m")]
    [string] $models,
    [Parameter(Mandatory = $false)]
    [Alias("h")]
    [switch] $help
)

if ($help) {
    Get-Help .\listAIQuotas.ps1 -Detailed
    exit
}

function Get-Quotas() {
    $fetched_quotas_table = @()

    foreach ($location in $locations) {
        Write-Host "Fetching quotas for location $location..."
        try {
            $usages = (az cognitiveservices usage list --location $location) | ConvertFrom-Json
            $models = (az cognitiveservices model list --location $location) | ConvertFrom-Json
        }
        catch {
            Write-Host "Failed to fetch quotas for location $location : $_"
            break
        }

        foreach ($usage in $usages) {
            $modelName = $usage.name.value
            # continue if kind.sku.name not in cadidate_models
            $candidate = $candidate_models | Where-Object { $modelName -eq $_.kind + "." + $_.sku + "." + $_.name }
            if (!$candidate) {
                continue
            }

            # Find the candidate model in the list of models and get the available versions
            $available_versions = @()
            $models | ForEach-Object {
                $model = $_
                $skuMatch = $model.model.skus | Where-Object { $_.name -eq $candidate.sku }
                if ($model.model.name -eq $candidate.name -and $model.kind -eq $candidate.kind -and $skuMatch) {
                    if ($candidate.versions -contains '*' -or $candidate.versions -contains $model.model.version) {
                        $available_versions += $model.model.version
                    }
                }
            }
            # Skip if no available versions
            if ($available_versions.Count -eq 0) {
                continue
            }

            $currentValue = $usage.currentValue
            $limit = $usage.limit
            $fetched_quotas_table += [PSCustomObject]@{
                "Location"           = $location
                "Model"              = "$($candidate.kind).$($candidate.sku).$($candidate.name)"
                "Available Versions" = $available_versions -join ", "
                "Remaining Quotas"   = $($limit - $currentValue).ToString()
                "Total Quotas"       = $limit.ToString()
            }
        }
    }
    return $fetched_quotas_table
}

function Check_Az() {
    # Check if Azure CLI is installed. If not, prompt the user to install it
    $azCli = Get-Command az -ErrorAction SilentlyContinue
    if (-not $azCli) {
        $installCli = Read-Host "Azure CLI is not installed. Do you want to install it now? (Y/N)"
        if ($installCli -eq 'Y') {
            Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi
            Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi'
            Remove-Item .\AzureCLI.msi
            Write-Host "Azure CLI has been installed. Please refresh your terminal and login to your Azure account using 'az login' before running this script"
            exit
        }
        else {
            Write-Host "This script requires Azure CLI. Please install it and run the script again."
            exit
        }
    }
}

# list of locations in which to look for candidate models
$locations = @( "australiaeast", "eastus", "eastus2", "francecentral", "norwayeast", "swedencentral", "uksouth")

# list of candidate models we need
$candidate_models = @()
if ($models) {
    $modelList = $models -split ' '
    foreach ($model in $modelList) {
        $modelParts = $model -split ':'
        $kindSkuName = $modelParts[0] -split '\.'
        $versions = if ($modelParts[1]) { $modelParts[1] -split ',' } else { @("*") }
        $candidate_models += @{
            "name"     = $kindSkuName[2]
            "versions" = $versions
            "sku"      = $kindSkuName[1]
            "kind"     = $kindSkuName[0]
        }
    }
}
else {
    # Default candidate models
    $candidate_models = @(
        @{
            "name"     = "gpt-35-turbo"
            "versions" = @("1106", "0301", "0613")
            "sku"      = "Standard"
            "kind"     = "OpenAI"
        },
        @{
            "name"     = "gpt-4"
            "versions" = @("1106-Preview")
            "sku"      = "Standard"
            "kind"     = "OpenAI"
        }
    )
}

Check_Az

try {
    $account = az account show | ConvertFrom-Json
}
catch {
    Write-Host "Failed to get account: $_"
    exit
}
# exit if not logged in
if (!$account -or !$account.id) {
    Write-Host "Please login to your Azure account using 'az login' before running this script"
    exit
}

$originSubscription = $account.id

# Set the subscription if provided
$switchSubscription = $false
if ($subscription -and $subscription -ne $originSubscription) {
    az account set -s $subscription
    Write-Host "Fetching quotas for the candidate models in the candidate locations for subscription $($subscription)"
    $switchSubscription = $true
}
else {
    Write-Host "Fetching quotas for the candidate models in the candidate locations for subscription $($originSubscription)"
}

$quotas = Get-Quotas
Write-Output $quotas | Format-Table -AutoSize -Wrap

# Switch back to the original subscription if we switched
if ($switchSubscription) {
    az account set -s $originSubscription
}
