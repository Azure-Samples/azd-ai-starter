#!/bin/bash

# This script lists the remaining quotas for the specified models in the specified locations.
# The script requires Azure CLI to be installed and logged in.
#
# How to run:
# az login
# az account set --subscription "<subscription_id>"
# bash ./listAIQuotas.sh
# bash ./listAIQuotas.sh -s "<subscription_id>"
# bash ./listAIQuotas.sh -m "OpenAI.Standard.gpt-35-turbo:1106,0301,0613" -s "<subscription_id>"
# bash ./listAIQuotas.sh -m "OpenAI.Standard.gpt-35-turbo OpenAi.Standard.gpt-4:1106-Preview" -s "<subscription_id>"

set -e
set -u

get_quotas() {
    local fetched_quotas_table=("location,Model,Available Version,Remaining Quotas,Total Quotas")
    
    for location in "${locations[@]}"; do
        echo "Fetching quotas for location $location..." >&2
        
        local usages=$(az cognitiveservices usage list --location $location --query "[].{name: name.value, currentValue: currentValue, limit: limit}" -o tsv)
        local models=$(az cognitiveservices model list --location $location --query "[].{name: model.name, sku: model.skus[0].name, kind: kind, version: model.version}" -o tsv)
        
        IFS=$'\n'
        for usage in $usages; do
            local model_fullname=$(echo $usage | cut -f1)
            local current_value=$(echo $usage | cut -f2)
            local limit=$(echo $usage | cut -f3)
            
            for candidate in "${candidate_models[@]}"; do
                if [[ "$candidate" == *":"* ]]; then
                    # If candidate contains ":", split it into candidate_model and versions
                    candidate_model_name="${candidate%%:*}"
                    versions="${candidate#*:}"
                else
                    # If candidate does not contain ":", set candidate_model to candidate and versions to "*"
                    candidate_model_name="$candidate"
                    versions="*"
                fi
                
                if [[ $candidate_model_name != $model_fullname ]]; then
                    continue
                fi
                
                # Find the candidate model in the list of models and get the available versions
                available_versions=()
                for model in $models; do
                    local model_name=$(echo $model | cut -f1)
                    local sku=$(echo $model | cut -f2)
                    local kind=$(echo $model | cut -f3)
                    local version=$(echo $model | cut -f4)
                    if [[  $model_fullname == "$kind.$sku.$model_name" ]]; then
                        if [[ "$versions" == *"*"* ]] || echo "$versions" | grep -q -w "$version"; then
                            available_versions+=("$version")
                        fi
                    fi
                done
                
                # Skip if no available versions
                if [ ${#available_versions[@]} -eq 0 ]; then
                    continue
                fi
                
                available_versions_str=$(printf "; %s" "${available_versions[@]}")
                available_versions_str=${available_versions_str:1}
                fetched_quotas_table+=("$location,$model_fullname,$available_versions_str,$(echo "$limit - $current_value" | bc),$limit")

                # skip the rest of the candidate_models
                break
            done
        done
        unset IFS
    done

    if [ ${#fetched_quotas_table[@]} -eq 1 ]; then
        echo "No quotas found for the candidate models" >&2
        return
    fi
    printf "%s\n" "${fetched_quotas_table[@]}"
}

check_az() {
    # Check if Azure CLI is installed. If not, prompt the user to install it
    if ! command -v az &> /dev/null; then
        echo "Azure CLI is not installed. Would you like to install it now? (Y/N)" >&2
        read answer
        if [ "$answer" == "Y" ]; then
            curl -L https://aka.ms/InstallAzureCli | bash
            echo "Azure CLI has been installed. Please login using 'az login' and restart the script." >&2
            exit 0
        else
            echo "Azure CLI is required for this script to run. Exiting." >&2
            exit 1
        fi
    fi
    
}


# list of locations in which to look for candidate models
locations=("australiaeast" "eastus" "eastus2" "francecentral" "norwayeast" "swedencentral" "uksouth")

# list of candidate models we need
candidate_models=(
    "OpenAI.Standard.gpt-35-turbo:*"
    "OpenAI.Standard.gpt-4:1106-Preview"
)

subscription=""

while (( "$#" )); do
    case "$1" in
        -m|--models)
            candidate_models=($2)
            shift 2
        ;;
        -s|--subscription)
            subscription="$2"
            shift 2
        ;;
        -h|--help)
            echo "Usage: $0 [-m|--models <model>] [-s|--subscription <subscription>]"
            echo "Options:"
            echo "  -m|--models <model>         List of candidate models to check. Default: OpenAI.Standard.gpt-35-turbo:* OpenAI.Standard.gpt-4:1106-Preview"
            echo "  -s|--subscription <subscription>  Azure subscription ID to use. Default: Current subscription"
            echo "  -h|--help                 Show help"
            exit 0
        ;;
        *)
            echo "Invalid option: $1" 1>&2
            exit 1
        ;;
    esac
done

check_az

original_subscription=$(az account show --query id -o tsv 2>/dev/null)

# Exit if not logged in
if [ -z "$original_subscription" ]; then
    echo "Please login to your Azure account using 'az login' before running this script" >&2
    exit 1
fi

# Set the subscription if provided
switched_subscription=false
if [ -n "$subscription" ] && [ "$subscription" != "$original_subscription" ]; then
    az account set --subscription "$subscription"
    switched_subscription=true
    echo "Fetching quotas for the candidate models in the candidate locations for subscription $subscription"
else
    echo "Fetching quotas for the candidate models in the candidate locations for subscription $original_subscription"
fi

quotas=$(get_quotas)
printf "%s\n" "${quotas[@]}" | column -s, -t

# Switch back to the original subscription if we switched
if [ -n "$switched_subscription" ]; then
    az account set --subscription "$original_subscription"
fi
