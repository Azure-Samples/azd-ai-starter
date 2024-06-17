<#
.SYNOPSIS
    This script uses Azure CLI to list the available API versions for the specified resource type and namespace. 
.DESCRIPTION
    This script lists the available API versions for the specified resource type and namespace.
    The script requires Azure CLI to be installed and logged in.
.EXAMPLE
    ./listApiVersions.ps1
.EXAMPLE
    ./listApiVersions.ps1 -r "accounts" -n "Microsoft.CognitiveServices"
.PARAMETER resourceType
    The resource type to fetch the API versions for. If not provided, the script will use the default value "accounts".
.PARAMETER namespace
    The namespace to fetch the API versions for. If not provided, the script will use the default value "Microsoft.CognitiveServices".
.PARAMETER help
    Show the help message.
#>
param(
    [Alias("r")]
    [string]$resourceType = "accounts",
    [Alias("n")]
    [string]$namespace = "Microsoft.CognitiveServices",
    [Alias("h")]
    [switch]$help
)

if ($help) {
    Get-Help .\listApiVersion.ps1 -Detailed
    exit
}

# Fetch API versions 
$apiVersions = az provider show --namespace ${namespace} --query "resourceTypes[?resourceType=='${resourceType}'].apiVersions[]" | ConvertFrom-Json

# Get the latest stable version
$latestStableVersion = $apiVersions | Where-Object { $_ -notlike "*-preview" } | Select-Object -First 1

# Print versions
Write-Host "API Versions for ${namespace}/${resourceType}:"
foreach ($version in $apiVersions) {
    if ($version -eq $latestStableVersion) {
        # Print latest stable version in bold green
        Write-Host ([char]27 + "[1m$version [Latest stable]" + [char]27 + "[0m") -ForegroundColor Green
    } else {
        Write-Host $version
    }
}
