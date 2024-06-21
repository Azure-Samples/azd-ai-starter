import os
import argparse
import subprocess
import logging
import yaml

azure_dev_workflow_file_path = ".github/workflows/azure-dev.yml"
ci_workflow_file_path = ".github/workflows/pr-gate.yml"
change_log_file_path = "CHANGELOG.md"
code_of_conduct_file_path = ".gethub/CODE_OF_CONDUCT.md"
contributing_file_path = "CONTRIBUTING.md"
issue_template_file_path = ".github/ISSUE_TEMPLATE.md"
license_file_path = "LICENSE"
readme_file_path = "README.md"
security_file_path = "SECURITY.md"
infra_bicep_file_path = "infra/main.bicep"
infra_yaml_file_path = "azure.yaml"

devcontainer_folder_path = ".devcontainer"
cicd_workflow_folder_path = ".github/workflows"

# The H2 tag list to be checked in README.md
readme_h2_tags = [
    "## Features",
    "## Getting Started",
    "## Guidance",
    "## Resources"
]

# The list of files need to be check for existence
existence_check_files = [
    contributing_file_path,
    change_log_file_path,
    license_file_path,
    readme_file_path,
    security_file_path,
    infra_bicep_file_path,
    infra_yaml_file_path,
    ci_workflow_file_path
]

repository_management_files = [
    readme_file_path,
    license_file_path,
    security_file_path,
    code_of_conduct_file_path,
    contributing_file_path,
    issue_template_file_path,
]

source_code_structure_files = [
    azure_dev_workflow_file_path,
    ci_workflow_file_path,
    infra_bicep_file_path,
    infra_yaml_file_path,
]

source_code_structure_folders = [
    devcontainer_folder_path
]

security_actions = ['microsoft/security-devops-action',
                    'github/codeql-action/upload-sarif']

line_delimiter = "\n"


def check_for_azd_down(folder_path):
    logging.debug(f"Checking with azd down...")
    try:
        command = f"azd down --force --purge"
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, shell=True)
        logging.debug(f"{result.stdout}")
        return True, f"- [x] azd down",
    except subprocess.CalledProcessError as e:
        logging.debug(f"{e.stdout}")
        message = []
        message.append(
            f"- [ ] azd down")
        message.append(f"Error: {e.stdout}")
        return False, line_delimiter.join(message),


def check_for_azd_up(folder_path):
    logging.debug(f"Checking with azd up...")
    try:
        command = f"azd up --no-prompt"
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, shell=True)
        logging.debug(f"{result.stdout}")
        return True, f"- [x] azd up",
    except subprocess.CalledProcessError as e:
        logging.debug(f"{e.stdout}")
        message = []
        message.append(
            f"- [ ] azd up")
        message.append(f"Error: {e.stdout}")
        return False, line_delimiter.join(message),


def check_for_bicep_lint(folder_path):
    logging.debug(f"Checking with az bicep build...")
    try:
        command = f"az bicep build --file {os.path.join(folder_path, infra_bicep_file_path)} --stdout"
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, shell=True)
        logging.debug(f"{result.stdout}")
        return True, f"- [x] {infra_bicep_file_path} content validation.",
    except subprocess.CalledProcessError as e:
        logging.warning(f"{e.stderr}")
        message = []
        message.append(
            f"- [ ] {infra_bicep_file_path} content validation.")
        message.append(f"Error: {e}")
        return False, line_delimiter.join(message),


def check_for_actions_in_workflow_file(repo_path, file_name, actions):
    logging.debug(f"Checking for steps in {file_name}...")
    result = True
    message = []

    with open(os.path.join(repo_path, file_name), 'r') as file:
        content = yaml.safe_load(file)

    def check_steps(steps, action):
        for step in steps:
            if isinstance(step, dict) and 'uses' in step:
                used_action = step['uses'].split('@')[0]
                if used_action == action:
                    return True
        return False

    if 'jobs' in content:
        for job in content['jobs'].values():
            if 'steps' in job:
                for action in actions:
                    if not check_steps(job['steps'], action):
                        result = result and False
                        message.append(
                            f"Error: {action} is missing in {file_name}.")
    return result, line_delimiter.join(message)


def find_cicd_workflow_file(repo_path):
    # return all yaml files in the /gethub/workflows folder as a list
    result, message = check_folder_existence(
        repo_path, cicd_workflow_folder_path)
    list = []
    if result:
        list = [f for f in os.listdir(os.path.join(
            repo_path, cicd_workflow_folder_path)) if f.endswith('.yml')]

    logging.debug(f"Found {len(list)} workflow files in {repo_path}.")
    return list


def check_folder_existence(repo_path, folder_name):
    logging.debug(f"Checking for {folder_name}...")
    message = []
    if not os.path.isdir(os.path.join(repo_path, folder_name)):
        message.append(f"- [ ] {folder_name} is in place.")
        message.append(f"Error: {folder_name} is missing.")
        return False, line_delimiter.join(message)
    else:
        message.append(f"- [x] {folder_name} is in place.")
        return True, line_delimiter.join(message)


def check_file_existence(repo_path, file_name, h2_tags=None):
    logging.debug(f"Checking for {file_name}...")
    message = []
    if not os.path.isfile(os.path.join(repo_path, file_name)):
        message.append(f"- [ ] {file_name} is in place.")
        message.append(f"Error: {file_name} is missing.")
        return False, line_delimiter.join(message)
    else:
        result = True
        subMessage = []
        if h2_tags is not None:
            with open(os.path.join(repo_path, file_name), 'r') as file:
                content = file.read()
                for tag in h2_tags:
                    if tag not in content:
                        result = result and False
                        subMessage.append(
                            f"Error: {tag} is missing in {file_name}.")
            file.close()

        if result == False:
            message.append(f"- [ ] {file_name} is in place.")
            message.extend(subMessage)
        else:
            message.append(f"- [x] {file_name} is in place.")
        return result, line_delimiter.join(message)


def check_repository_management(repo_path):
    final_result = True
    final_message = []
    final_message.append("## Repository Management:")

    for file_name in repository_management_files:
        tags_list = None
        if file_name == readme_file_path:
            tags_list = readme_h2_tags

        result, message = check_file_existence(repo_path, file_name, tags_list)
        final_result = final_result and result
        final_message.append(message)
    return final_result, line_delimiter.join(final_message)


def check_for_source_code_structure(repo_path):
    final_result = True
    final_message = []
    final_message.append("## Source code structure and conventions:")

    for file_name in source_code_structure_files:
        tags_list = None
        if file_name == readme_file_path:
            tags_list = readme_h2_tags

        result, message = check_file_existence(repo_path, file_name, tags_list)
        final_result = final_result and result
        final_message.append(message)

    for file_name in source_code_structure_folders:
        result, message = check_folder_existence(repo_path, file_name)
        final_result = final_result and result
        final_message.append(message)

    return final_result, line_delimiter.join(final_message)


def check_for_functional_requirements(repo_path, check_azd_up, check_azd_down):
    final_result = True
    final_message = []
    final_message.append("## Functional Requirements:")

    # check for the existence of the files
    if check_azd_up:
        result, message = check_for_azd_up(repo_path)
        final_result = final_result and result
        final_message.append(message)
        if check_azd_down:
            result, message = check_for_azd_down(repo_path)
            final_result = final_result and result
            final_message.append(message)
    else:
        result, message = check_for_bicep_lint(repo_path)
        final_result = final_result and result
        final_message.append(message)

    return final_result, line_delimiter.join(final_message)


def check_for_security_requirements(repo_path):
    final_result = True
    final_message = []
    final_message.append("## Security Requirements:")

    # check for security action
    security_result = False
    security_message = []
    list = find_cicd_workflow_file(repo_path)
    for file in list:
        result, message = check_for_actions_in_workflow_file(
            repo_path, os.path.join(cicd_workflow_folder_path, file), security_actions)
        security_result = security_result or result
        security_message.append(message)

    final_result = final_result and security_result
    if security_result:
        final_message.append(
            f"- [x] microsoft/security-devops-action is integrated to the CI/CD pipeline.")
    else:
        final_message.append(
            f"- [ ] microsoft/security-devops-action is integrated to the CI/CD pipeline.")
        final_message.extend(security_message)

    return final_result, line_delimiter.join(final_message)


def internal_validator(repo_path, check_azd_up, check_azd_down):
    if not os.path.isdir(repo_path):
        raise Exception(f"Error: The path {
                        repo_path} is not a valid directory.")
        return

    final_result = True
    final_message = []

    result, message = check_repository_management(repo_path)
    final_result = final_result and result
    final_message.append(message)

    result, message = check_for_source_code_structure(repo_path)
    final_result = final_result and result
    final_message.append(message)

    result, message = check_for_functional_requirements(
        repo_path, check_azd_up, check_azd_down)
    final_result = final_result and result
    final_message.append(message)

    result, message = check_for_security_requirements(repo_path)
    final_result = final_result and result
    final_message.append(message)

    return final_result, line_delimiter.join(final_message)


def main():
    parser = argparse.ArgumentParser(
        description="Validate the repo with the standards of https://azure.github.io/ai-apps/.")
    parser.add_argument('repo_path', type=str,
                        help="The path to the repo to validate.")
    parser.add_argument('--azdup', action='store_true',
                        help="Check infra code with azd up.")
    parser.add_argument('--azddown', action='store_true',
                        help="Check infra code with azd up.")
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug logging.")
    parser.add_argument('--output', type=str)

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(message)s', level=log_level)

    logging.debug(f"Repo path: {args.repo_path} azdup: {args.azdup} azddown: {
                  args.azddown} debug: {args.debug} output: {args.output}")

    result, message = internal_validator(
        args.repo_path, args.azdup, args.azddown)

    if result:
        message = f"# AI Gallery Standard Validation: PASSED\n{message}"
    else:
        message = f"# AI Gallery Standard Validation: FAILED\n{message}"

    logging.warning(message)

    if args.output:
        with open(args.output, 'w') as file:
            file.write(message)
        file.close()

    # if not result:
    #    raise Exception(f"Validation failed as following: \n {message}")


if __name__ == "__main__":
    main()
