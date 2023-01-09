import github
import yaml
import hashlib
import time
import argparse
import ruamel.yaml

def set_branch_name() -> str:
    """Generates a unique branch name for the pull request."""
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode("utf-8"))
    branch_name = "MagicBot_" + hash.hexdigest()[:10]
    return branch_name
    

def load_credentials() -> dict:
    """Loads credentials from github settings."""                     
    with open("credentials.yml") as file:
        creds = yaml.load(file, Loader=yaml.FullLoader)
    return creds


def get_github_client(access_token: str) -> github.Github:
    """Returns a Github client."""
    return github.Github(access_token)


def load_configurations() -> dict:
    """Loads configurations from package_manager.yml."""
    with open("package_manager.yml") as file:
        config = ruamel.yaml.load(
            file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True
        )
    return config


def setup_repo(client: github.Github, repo_name: str, branch_name: str):
    """Creates a new branch on the repo and returns the repo object."""
    repo = client.get_repo("bsd/" + repo_name)
    try:
        master_sha = repo.get_branch(branch="master").commit.sha
        default_branch = "master"
    except:
        master_sha = repo.get_branch(branch="main").commit.sha
        default_branch = "main"
    repo.create_git_ref(ref="refs/heads/" + branch_name, sha=master_sha)
    return repo, default_branch


def update_packages(
    repo: github.Repository.Repository, branch_name: str, config: dict) -> None:
    """Updates the packages.yml file."""
    try:
        packages_content = repo.get_contents("packages.yml")
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
        print("'packages.yml' not found in repo.")


def update_project(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    """Updates the dbt_project.yml file."""
    project_content = repo.get_contents("dbt_project.yml")
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

def open_pull_request(
    repo: github.Repository.Repository, branch_name: str, default_branch: str
) -> None:
    body = """
    #### This pull request was created automatically 🎉

    Before merging this PR:
    - [ ] Verify that the dbt project runs in development mode
    - [ ] Run dbt-arc-functions create_or_update_standard_models.py if new marts were added
    """

    pr = repo.create_pull(
        try:
            title="Updating dbt version",
            body=body,
            head=branch_name,
            base=default_branch,
        except: github.GithubException:
            print("Pull request already exists.")
    )
    
    print(pr.html_url)


def main():
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
        open_pull_request(repo, branch_name, default_branch)


if __name__ == "__main__":
    main()
