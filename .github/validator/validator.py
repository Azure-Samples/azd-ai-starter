import os
import argparse
import subprocess
import logging
import yaml
from sarif import loader

azure_dev_workflow_file_path = ".github/workflows/azure-dev.yml"
ci_workflow_file_path = ".github/workflows/pr-gate.yml"
change_log_file_path = "CHANGELOG.md"
code_of_conduct_file_path = ".github/CODE_OF_CONDUCT.md"
contributing_file_path = "CONTRIBUTING.md"
issue_template_file_path = ".github/ISSUE_TEMPLATE.md"
license_file_path = "LICENSE"
readme_file_path = "README.md"
security_file_path = "SECURITY.md"
infra_yaml_file_path = "azure.yaml"

infra_folder_path = "infra"
devcontainer_folder_path = ".devcontainer"
cicd_workflow_folder_path = ".github/workflows"

# The H2 tag list to be checked in README.md
readme_h2_tags = [
    "## Features",
    "## Getting Started",
    "## Guidance",
    "## Resources"
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
#   ci_workflow_file_path,
    infra_yaml_file_path,
]

source_code_structure_folders = [
    infra_folder_path,
    devcontainer_folder_path
]

severity_error = "error"
severity_error_exceptions = ["AZR-000283"]

expected_topics = ["azd-templates", "ai-azd-templates"]

security_actions = ['microsoft/security-devops-action',
                    'github/codeql-action/upload-sarif']

line_delimiter = "\n"
details_help_link = "https://aka.ms/ai-template-standards"


class Signs:
    CHECK = ":heavy_check_mark:"
    BLOCK = ":x:"
    WARNING = ":warning:"


how_to_fix = "## <i>How to fix?</i>\n<b>The full Definition of Done of the AI-Gallery template and fix approached can be found [HERE]({detail_link}).</b>".format(
    detail_link=details_help_link)

final_result_format = "# AI Gallery Standard Validation: {{result}} \n{{message}}\n\n{end_message}".format(
    link=details_help_link, end_message=how_to_fix)


class ItemResultFormat:
    PASS = "<details><summary>{sign} <b>{{message}}</b>.</summary></details>".format(
        sign=Signs.CHECK)
    FAIL = "<details><summary>{sign} <b>{{message}}</b>. <a href={detail_link}>[How to fix?]</a></summary>\n\n{{detail_messages}}\n\n</details>".format(
        sign=Signs.BLOCK, detail_link=details_help_link)
    WARNING = "<details><summary>{sign} <b>{{message}}</b>. <a href={detail_link}>[How to fix?]</a></summary>\n\n{{detail_messages}}\n\n</details>".format(
        sign=Signs.WARNING, detail_link=details_help_link)


def check_msdo_result(msdo_result_file):
    logging.debug(f"Checking for msdo result: {msdo_result_file}...")
    result = True
    message = ""

    if msdo_result_file is not None and os.path.isfile(msdo_result_file):
        subMessages = []
        sarif_data = loader.load_sarif_file(msdo_result_file)
        report = sarif_data.get_records_grouped_by_severity()
        for severity in report:
            items_of_severity = report.get(severity, [])
            for item in items_of_severity:
                if severity == severity_error and item['Code'] not in severity_error_exceptions:
                    result = result and False
                    subMessages.append(
                        f"- {severity}: {item['Code']} - {item['Description']}")
                elif item['Code'] in severity_error_exceptions:
                    subMessages.append(
                        f"- warning: {item['Code']} - {item['Description']}")
                else:
                    subMessages.append(
                        f"- {severity}: {item['Code']} - {item['Description']}")

        if result and len(subMessages) == 0:
            message = ItemResultFormat.PASS.format(
                message="Security scan")
        elif len(subMessages) > 0:
            message = ItemResultFormat.WARNING.format(
                message="Security scan", detail_messages=line_delimiter.join(subMessages))
        else:
            message = ItemResultFormat.FAIL.format(
                message="Security scan", detail_messages=line_delimiter.join(subMessages))

    else:
        result = False
        message = ItemResultFormat.FAIL.format(
            message="Security scan", detail_messages=f"- Error: Scan result is missing.")

    return result, message


def check_for_azd_down(folder_path):
    logging.debug(f"Checking with azd down...")
    original_directory = os.getcwd()
    try:
        os.chdir(folder_path)
        command = f"azd down --force --purge"
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, shell=True)
        logging.debug(f"{result.stdout}")
        return True, ItemResultFormat.PASS.format(message="azd down")
    except subprocess.CalledProcessError as e:
        logging.debug(f"{e.stdout}")
        return False, ItemResultFormat.FAIL.format(message="azd down", detail_messages=f"Error: {e.stdout}")
    finally:
        os.chdir(original_directory)


def check_for_azd_up(folder_path):
    logging.debug(f"Checking with azd up...")
    original_directory = os.getcwd()
    try:
        os.chdir(folder_path)
        command = f"azd up --no-prompt"
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, shell=True)
        logging.debug(f"{result.stdout}")
        return True, ItemResultFormat.PASS.format(message="azd up")
    except subprocess.CalledProcessError as e:
        logging.debug(f"{e.stdout}")
        return False, ItemResultFormat.FAIL.format(message="azd up", detail_messages=f"Error: {e.stdout}")
    finally:
        os.chdir(original_directory)


def check_for_actions_in_workflow_file(repo_path, file_name, actions):
    logging.debug(f"Checking for steps in {file_name}...")
    result = True
    messages = []

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
                        messages.append(
                            f"- Error: {action} is missing in {file_name}.")
    return result, line_delimiter.join(messages)


def find_cicd_workflow_file(repo_path):
    # return all yaml files in the /github/workflows folder as a list
    result, message = check_folder_existence(
        repo_path, cicd_workflow_folder_path)
    list = []
    if result:
        list = [f for f in os.listdir(os.path.join(
            repo_path, cicd_workflow_folder_path)) if f.endswith('.yml')]

    logging.debug(f"Found {len(list)} workflow files in {repo_path}.")
    return list


def check_topic_existence(actual_topics, expected_topics):
    logging.debug(f"Checking for topics...")
    messages = []
    result = True

    subMessages = []
    if actual_topics is None:
        result = False
        subMessages.append(f"- Error: topics string is NULL.")
    else:
        actual_topics_list = actual_topics.split(",")
        for topic in expected_topics:
            if topic not in actual_topics_list:
                result = result and False
                subMessages.append(f"- Error: {topic} is missing in topics.")

    if result:
        messages.append(ItemResultFormat.PASS.format(
            message=f"Topics on repo contains {expected_topics}"))
    else:
        messages.append(ItemResultFormat.FAIL.format(
            message=f"Topics on repo contains {expected_topics}", detail_messages=line_delimiter.join(subMessages)))

    return result, line_delimiter.join(messages)


def check_folder_existence(repo_path, folder_name):
    logging.debug(f"Checking for {folder_name}...")
    messages = []
    if not os.path.isdir(os.path.join(repo_path, folder_name)):
        messages.append(ItemResultFormat.FAIL.format(
            message=f"{folder_name} Folder", detail_messages=f"- Error: {folder_name} folder is missing."))
        return False, line_delimiter.join(messages)
    else:
        messages.append(ItemResultFormat.PASS.format(
            message=f"{folder_name} Folder"))
        return True, line_delimiter.join(messages)


def check_file_existence(repo_path, file_name, h2_tags=None):
    logging.debug(f"Checking for {file_name}...")
    messages = []
    if not os.path.isfile(os.path.join(repo_path, file_name)):
        messages.append(ItemResultFormat.FAIL.format(
            message=f"{file_name} File", detail_messages=f"- Error: {file_name} file is missing."))
        return False, line_delimiter.join(messages)
    else:
        result = True
        subMessages = []
        if h2_tags is not None:
            with open(os.path.join(repo_path, file_name), 'r') as file:
                content = file.read()
                for tag in h2_tags:
                    if tag not in content:
                        result = result and False
                        subMessages.append(
                            f"- Error: {tag} is missing in {file_name}.")
            file.close()

        if result == False:
            messages.append(ItemResultFormat.FAIL.format(
                message=f"{file_name} File", detail_messages=line_delimiter.join(subMessages)))
        else:
            messages.append(ItemResultFormat.PASS.format(
                message=f"{file_name} File"))
        return result, line_delimiter.join(messages)


def check_repository_management(repo_path, topics):
    final_result = True
    final_messages = [""]
    final_messages.append("## Repository Management:")

    for file_name in repository_management_files:
        tags_list = None
        if file_name == readme_file_path:
            tags_list = readme_h2_tags

        result, message = check_file_existence(repo_path, file_name, tags_list)
        final_result = final_result and result
        final_messages.append(message)

    # sample topics: "azd-templates,azure"
    result, message = check_topic_existence(topics, expected_topics)
    final_result = final_result and result
    final_messages.append(message)

    return final_result, line_delimiter.join(final_messages)


def check_source_code_structure(repo_path):
    final_result = True
    final_messages = [""]
    final_messages.append("## Source code structure and conventions:")

    for file_name in source_code_structure_files:
        tags_list = None
        if file_name == readme_file_path:
            tags_list = readme_h2_tags

        result, message = check_file_existence(repo_path, file_name, tags_list)
        final_result = final_result and result
        final_messages.append(message)

    for file_name in source_code_structure_folders:
        result, message = check_folder_existence(repo_path, file_name)
        final_result = final_result and result
        final_messages.append(message)

    return final_result, line_delimiter.join(final_messages)


def check_functional_requirements(repo_path, check_azd_up, check_azd_down):
    final_result = True
    final_messages = [""]
    final_messages.append("## Functional Requirements:")

    # check for the existence of the files
    if check_azd_up:
        result, message = check_for_azd_up(repo_path)
        final_result = final_result and result
        final_messages.append(message)
        if check_azd_down:
            result, message = check_for_azd_down(repo_path)
            final_result = final_result and result
            final_messages.append(message)

    return final_result, line_delimiter.join(final_messages)


def check_security_requirements(repo_path, msdo_result_file):
    final_result = True
    final_messages = [""]
    final_messages.append("## Security Requirements:")

    # check for security action
    msdo_integrated_result = False
    msdo_integrated_messages = []
    msdo_integrated_messages.append(
        "Not found security check related actions in the CI/CD pipeline.")
    list = find_cicd_workflow_file(repo_path)
    for file in list:
        result, message = check_for_actions_in_workflow_file(
            repo_path, os.path.join(cicd_workflow_folder_path, file), security_actions)
        msdo_integrated_result = msdo_integrated_result or result
        msdo_integrated_messages.append(message)

    final_result = final_result and msdo_integrated_result
    if msdo_integrated_result:
        final_messages.append(ItemResultFormat.PASS.format(
            message="microsoft/security-devops-action is integrated to the CI/CD pipeline"))
    else:
        final_messages.append(ItemResultFormat.WARNING.format(message="microsoft/security-devops-action is integrated to the CI/CD pipeline",
                                                              detail_messages=line_delimiter.join(msdo_integrated_messages)))

    result, message = check_msdo_result(msdo_result_file)
    final_result = final_result and result
    final_messages.append(message)

    return final_result, line_delimiter.join(final_messages)


def internal_validator(repo_path, check_azd_up, check_azd_down, topics, msdo_result_file):
    if not os.path.isdir(repo_path):
        raise Exception(f"Error: The path {
                        repo_path} is not a valid directory.")
        return

    final_result = True
    final_message = []

    result, message = check_repository_management(repo_path, topics)
    final_result = final_result and result
    final_message.append(message)

    result, message = check_source_code_structure(repo_path)
    final_result = final_result and result
    final_message.append(message)

    result, message = check_functional_requirements(
        repo_path, check_azd_up, check_azd_down)
    final_result = final_result and result
    final_message.append(message)

    result, message = check_security_requirements(repo_path, msdo_result_file)
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
    parser.add_argument('--topics', type=str, help="The topics to be checked.")
    parser.add_argument('--msdoresult', type=str,
                        help="The output file path of microsoft security devops analysis.")
    parser.add_argument('--output', type=str, help="The output file path.")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(message)s', level=log_level)

    logging.debug(
        f"Repo path: {args.repo_path} azdup: {args.azdup} azddown: {args.azddown} debug: {args.debug} topics: {args.topics} msdo: {args.msdoresult} output: {args.output}")

    result, message = internal_validator(
        args.repo_path, args.azdup, args.azddown, args.topics, args.msdoresult)

    if result:
        message = final_result_format.format(result="PASSED", message=message)
    else:
        message = final_result_format.format(result="FAILED", message=message)

    logging.warning(message)

    if args.output:
        with open(args.output, 'w') as file:
            file.write(message)
        file.close()

    # if not result:
    #    raise Exception(f"Validation failed as following: \n {message}")


if __name__ == "__main__":
    main()
