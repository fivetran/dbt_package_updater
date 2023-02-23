"""This script updates the dbt version and package versions in all
    dbt projects in the bsd organization."""

import contextlib
import hashlib
import requests
from bs4 import BeautifulSoup
import time
from github import Github, GithubException, Repository


import ruamel.yaml

# TODO add a check to see if the dbt version is already the latest version


def set_branch_name() -> str:
    """Generates a unique branch name for the pull request."""
    hash_name = hashlib.sha1()
    hash_name.update(str(time.time()).encode("utf-8"))
    return f"MagicBot_{hash_name.hexdigest()[:10]}"  # 10 characters


def load_credentials(credentials_file: str) -> dict:
    """Loads credentials from a file."""
    with open(credentials_file, encoding='utf-8') as file:
        creds = ruamel.yaml.load(file, Loader=ruamel.yaml.Loader)
    return creds


def get_github_client(access_token: str) -> Github:
    """Returns a Github client."""
    return Github(access_token)


def load_configurations(config_file: str) -> dict:
    """Loads configurations from a file."""
    config_file = "package_manager.yml"
    with open(config_file, encoding='utf-8') as file:
        config = ruamel.yaml.load(
            file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True
        )
    return config


def setup_repo(client: Github, repo_name: str, branch_name: str):
    """Creates a new branch on the repo and returns the repo object."""
    repo = client.get_repo(f"bsd/{repo_name}")
    try:
        master_sha = repo.get_branch(branch="master").commit.sha
        default_branch = "master"
    except GithubException:
        master_sha = repo.get_branch(branch="main").commit.sha
        default_branch = "main"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=master_sha)
    return repo, default_branch


def find_file_in_repo(repo: Repository.Repository, filename: str):
    """Finds a file in a repo."""
    with contextlib.suppress(GithubException):
        # Look for the file in the root directory
        return repo.get_contents(filename)
    # If the file is not in the root directory, search for it in all subdir
    subdirs = [c.path for c in repo.get_contents("") if c.type == "dir"]
    for subdir in subdirs:
        with contextlib.suppress(GithubException):
            return repo.get_contents(f"{subdir}/{filename}")
    # If the file is not found anywhere, raise an exception
    raise GithubException(status=404, data={"message": f"{filename} not in {repo.full_name}"})


def get_latest_version(repo_name: str) -> str:
    '''Gets the latest version tag from a GitHub repository.'''
    url = f'https://api.github.com/repos/{repo_name}/tags'
    response = requests.get(url, timeout=(5, 30))
    if response.status_code == 200:
        if tags := response.json():
            latest_tag = max(tags, key=lambda x: x['name'])
            return latest_tag['name']
    return 'Version information not found.'


def update_packages(
    repo: Repository, branch_name: str, config: dict
) -> None:
    """Updates the packages.yml file."""
    try:
        packages_content = find_file_in_repo(repo, "packages.yml")
        packages = ruamel.yaml.load(
            packages_content.decoded_content,
            Loader=ruamel.yaml.RoundTripLoader,
            preserve_quotes=True,
        )

        for package in packages["packages"]:
            if "package" in package:
                name = package["package"]
                if name in config["packages"]:
                    package["version"] = config["packages"][name]
            if "git" in package:
                name = package["git"]
                if name in config["packages"]:
                    package["revision"] = config["packages"][name]
            if "git" in package and package["git"] == "https://github.com/bsd/dbt-arc-functions.git":
                # get latest tag revision from GitHub repository
                repo_name = "bsd/dbt-arc-functions"
                latest_version = get_latest_version(repo_name)
                # update packages.yml with latest version tag
                package["revision"] = latest_version

        repo.update_file(
            path=packages_content.path,
            message="Updating package dependendcies",
            content=ruamel.yaml.dump(packages, Dumper=ruamel.yaml.RoundTripDumper),
            sha=packages_content.sha,
            branch=branch_name,
        )
    except GithubException:
        print(f"'packages.yml' not found in {repo.full_name}")


def update_project(
    repo: Repository, branch_name: str, config: str
) -> None:
    """Updates the dbt_project.yml file."""
    try:
        project_content = find_file_in_repo(repo, "dbt_project.yml")
        project = ruamel.yaml.load(
            project_content.decoded_content,
            Loader=ruamel.yaml.RoundTripLoader,
            preserve_quotes=True,
            )

        # Update the require-dbt-version
        project["require-dbt-version"] = config["require-dbt-version"]

        # Update the project file
        repo.update_file(
            path=project_content.path,
            message="Updating require-dbt-version",
            content=ruamel.yaml.dump(project, Dumper=ruamel.yaml.RoundTripDumper),
            sha=project_content.sha,
            branch=branch_name,
        )

    except GithubException as github_exception:
        print(github_exception.data["message"])


def get_repo_contributors(repo: Repository.Repository) -> list:
    """Returns a list of repo contributors."""
    return [contributor.login for contributor in repo.get_contributors()]


def open_pull_request(
    repo: Repository.Repository, branch_name: str, default_branch: str, contributors: list
) -> None:
    '''Opens a pull request'''
    try:
        contributors = get_repo_contributors(repo)
        body = f"""
    #### This pull request was created
    #### automatically by bsd/dbt_project_updater 🎉
    Tagging contributors as FYI @{' @'.join(contributors)}

    Before merging this PR:
    - [ ] Verify that all the checks pass.
    - [ ] If revision adds new standard models,
            run `create_or_update_standard_models.py`
            in bsd/dbt-arc-functions repo.
    """
        pull_request = repo.create_pull(
                title="Updating dbt version",
                body=body,
                head=branch_name,
                base=default_branch,
        )
        print(f"Pull request created at {pull_request.html_url}")

    except GithubException:
        print(f"Pull request already exists in {repo.full_name}.")


def main():
    """Main function"""
    # Setup
    branch_name = set_branch_name()
    creds = load_credentials("credentials.yml")
    config = load_configurations("package_manager.yml")
    client = get_github_client(creds["access_token"])

    # Iterate through repos
    for repo_name in config["repositories"]:
        try:
            repo, default_branch = setup_repo(client, repo_name, branch_name)
            update_packages(repo, branch_name, config)
            update_project(repo, branch_name, config)
            contributors = get_repo_contributors(repo)
            open_pull_request(repo, branch_name, default_branch, contributors)
        except GithubException as github_exception:
            print(f"Error: {github_exception.data['message']}")

    # print success message
    print("Done!")
  
if __name__ == "__main__":
    main()
