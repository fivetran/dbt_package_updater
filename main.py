import github
import yaml
import hashlib
import time
import argparse


def set_branch_name() -> str:
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode("utf-8"))
    branch_name = "MagicBot_" + hash.hexdigest()[:10]
    return branch_name


def load_credentials() -> dict:
    with open("credentials.yml") as file:
        creds = yaml.load(file, Loader=yaml.FullLoader)
    return creds


def get_github_client(access_token: str) -> github.Github:
    return github.Github(access_token)


def load_configurations() -> dict:
    with open("package_manager.yml") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def setup_repo(
    client: github.Github, repo_name: str, branch_name: str
) -> github.Repository.Repository:
    repo = client.get_repo("Fivetran/" + repo_name)
    master_sha = repo.get_branch(branch="master").commit.sha
    repo.create_git_ref(ref="refs/heads/" + branch_name, sha=master_sha)
    return repo


def update_packages(
    repo: github.Repository.Repository, branch_name: str, config: dict
) -> None:
    try:
        packages_content = repo.get_contents("packages.yml")
        packages = yaml.load(packages_content.decoded_content, Loader=yaml.FullLoader)

        for package in packages["packages"]:
            name = package["package"]
            if name in config["packages"]:
                package["version"] = config["packages"][name]

        repo.update_file(
            path=packages_content.path,
            message="Updating package dependendcies",
            content=yaml.dump(packages, encoding="utf-8", default_flow_style=False),
            sha=packages_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        print("'packages.yml' not found in repo.")


def update_project(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    project_content = repo.get_contents("dbt_project.yml")
    project = yaml.load(project_content.decoded_content, Loader=yaml.FullLoader)
    project["require-dbt-version"] = config["require-dbt-version"]

    repo.update_file(
        path=project_content.path,
        message="Updating require-dbt-version",
        content=yaml.dump(project, encoding="utf-8", default_flow_style=False),
        sha=project_content.sha,
        branch=branch_name,
    )


def update_requirements(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    try:
        requirements_content = repo.get_contents("integration_tests/requirements.txt")
        repo.update_file(
            path=requirements_content.path,
            message="Updating dbt version in requirements.txt",
            content="dbt==" + str(config["ci-dbt-version"]),
            sha=requirements_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        repo.create_file(
            path="integration_tests/requirements.txt",
            message="Updating dbt version in requirements.txt",
            content="dbt==" + str(config["ci-dbt-version"]),
            branch=branch_name,
        )


def open_pull_request(repo: github.Repository.Repository, branch_name: str) -> None:
    body = """
    #### This pull request was created automatically 🎉

    Before merging this PR:
    - [ ] Verify that all the tests pass.
    - [ ] Tag a release 
    """

    pull = repo.create_pull(
        title="[MagicBot] Bumping package version",
        body=body,
        head=branch_name,
        base="master",
    )

    print(pull.html_url)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dbt-package-manager")
    parser.add_argument("--repo-type", required=True)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    # Setup
    branch_name = set_branch_name()
    creds = load_credentials()
    config = load_configurations()
    client = get_github_client(creds["access_token"])

    # Iterate through repos
    for repo_name in config["repositories"][args.repo_type]:
        repo = setup_repo(client, repo_name, branch_name)
        update_packages(repo, branch_name, config)
        update_project(repo, branch_name, config)
        update_requirements(repo, branch_name, config)
        open_pull_request(repo, branch_name)


if __name__ == "__main__":
    main()
