#!/bin/bash

# This script lists the API versions for the specified resource type in the specified namespace.
# The script requires Azure CLI to be installed and logged in.
#
# How to run:
# az login
# bash ./listApiVersions.sh
# bash ./listApiVersions.sh -r "<resourceType>" -n "<namespace>"

# Default values
resourceType="accounts"
namespace="Microsoft.CognitiveServices"

# Parse command line arguments
while (( "$#" )); do
    case "$1" in
        -r|--resourceType)
            resourceType="$2"
            shift 2
        ;;
        -n|--namespace)
            namespace="$2"
            shift 2
        ;;
        -h|--help)
            echo "Usage: $0 [-r|--resourceType <resourceType>] [-n|--namespace <namespace>]"
            echo "Options:"
            echo "  -r|--resourceType <resourceType>  The resource type to fetch the API versions for. Default: accounts"
            echo "  -n|--namespace <namespace>  The namespace to fetch the API versions for. Default: Microsoft.CognitiveServices"
            echo "  -h|--help  Show help"
            exit 0
        ;;
        *)
            echo "Invalid option: $1" 1>&2
            exit 1
        ;;
    esac
done

# Fetch API versions
apiVersions=$(az provider show --namespace ${namespace} --query "resourceTypes[?resourceType=='${resourceType}'].apiVersions[]" -o tsv)

# Find the latest stable version
stableVersions=($(for version in $apiVersions; do [[ $version != *"-preview"* ]] && echo $version; done))
latestStableVersion=${stableVersions[0]}

# Print versions
echo "API Versions for ${namespace}/${resourceType}:"
for version in $apiVersions; do
    if [ "$version" == "$latestStableVersion" ]; then
        version=$(echo $version | tr -d ' ')
        # Print latest stable version in bold green
        echo -e "\033[1;32m${version} [Latest stable]\033[0m"
    else
        echo "$version"
    fi
done
