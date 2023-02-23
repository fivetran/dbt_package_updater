"""This script updates the dbt version and package versions in all
    dbt projects in the bsd organization."""

import time
import hashlib
import github
import yaml


import ruamel.yaml

# TODO trigger this workflow after new dbt-arc-functions are released, and get
# latest revision from dbt-arc-functions repo
# TODO add a check to see if the dbt version is already the latest version
# TODO add a check to see if the package versions are
# already the latest version
# TODO add a step that pulls latest dbt-arc-functions revision
# TODO add a step that runs dbt-arc-functions
# create_or_update_standard_models.py if new marts were added


def set_branch_name() -> str:
    """Generates a unique branch name for the pull request."""
    hash_name = hashlib.sha1()
    hash_name.update(str(time.time()).encode("utf-8"))
    return f"MagicBot_{hash_name.hexdigest()[:10]}" 


def load_credentials() -> dict:
    """Loads credentials from github settings."""                   
    with open("credentials.yml", encoding='utf-8') as file:
        creds = yaml.load(file, Loader=yaml.FullLoader)
    return creds


def get_github_client(access_token: str) -> github.Github:
    """Returns a Github client."""
    return github.Github(access_token)


def load_configurations() -> dict:
    """Loads configurations from package_manager.yml."""
    with open("package_manager.yml", encoding='utf-8') as file:
        config = ruamel.yaml.load(
            file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True
        )
    return config


def setup_repo(client: github.Github, repo_name: str, branch_name: str):
    """Creates a new branch on the repo and returns the repo object."""
    repo = client.get_repo(f"bsd/{repo_name}")
    try:
        master_sha = repo.get_branch(branch="master").commit.sha
        default_branch = "master"
    except github.GithubException:
        master_sha = repo.get_branch(branch="main").commit.sha
        default_branch = "main"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=master_sha)
    return repo, default_branch


def update_packages(
        repo: github.Repository.Repository, branch_name: str, config: dict
            ) -> None:
    """Updates the packages.yml file."""
    try:
        root_content = repo.get_contents("")
        packages_content = None
        for item in root_content:
            if item.type == "file" and item.name == "packages.yml":
                packages_content = item
                break
            elif item.type == "dir":
                try:
                    packages_content = repo.get_contents(f"{item.path}/packages.yml")
                    break
                except github.GithubException:
                    continue
            if packages_content is None:
                raise github.GithubException(status=404, data={"message": "Not Found"})
      
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

        repo.update_file(
            path=packages_content.path,
            message="Updating package dependendcies",
            content=ruamel.yaml.dump(packages, Dumper=ruamel.yaml.RoundTripDumper),
            sha=packages_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        print(f"'packages.yml' not found in {repo.full_name}")


def update_project(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    """Updates the dbt_project.yml file."""
    try:
        root_content = repo.get_contents("")
        project_content = None
        for item in root_content:
            if item.type == "file" and item.name == "dbt_project.yml":
                project_content = item
                break
            elif item.type == "dir":
                try:
                    project_content = repo.get_contents(f"{item.path}/dbt_project.yml")
                    break
                except github.GithubException:
                    continue
            if project_content is None:
                raise github.GithubException(status=404, data={"message": "Not Found"})
       
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
    except github.GithubException:
        print(f"'dbt_project.yml' not found in {repo.full_name}")


def get_repo_contributors(repo: github.Repository.Repository) -> list:
    """Returns a list of repo contributors."""
    return [contributor.login for contributor in repo.get_contributors()]


def open_pull_request(
    repo: github.Repository.Repository, branch_name: str, default_branch: str
) -> None:
    '''Opens a pull request'''
    try:
        contributors = get_repo_contributors(repo)
        body = f"""
        #### This pull request was created automatically 🎉
        @{' @'.join(contributors)}
        
        Before merging this PR:
        - [ ] Verify that the dbt project runs in development mode
        - [ ] Run dbt-arc-functions create_or_update_standard_models.py if new marts were added
        """
        pr = repo.create_pull(
                title="Updating dbt version",
                body=body,
                head=branch_name,
                base=default_branch,
        )
        print(f"Pull request created at {pr.html_url}")

    except github.GithubException:
        print(f"Pull request already exists in {repo.full_name}.")


def main():
    '''Main function'''
    # Setup
    branch_name = set_branch_name()
    creds = load_credentials()
    config = load_configurations()
    client = get_github_client(creds["access_token"])

    # Iterate through repos
    for repo_name in config["repositories"]:
        repo, default_branch = setup_repo(client, repo_name, branch_name)
        update_packages(repo, branch_name, config)
        update_project(repo, branch_name, config)
        get_repo_contributors(repo)
        open_pull_request(repo, branch_name, default_branch)
    
    # print success message
    print("Done!")


if __name__ == "__main__":
    main()
