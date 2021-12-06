import github
import yaml
import hashlib
import time
import argparse
import ruamel.yaml


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
        config = ruamel.yaml.load(
            file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True
        )
    return config


def setup_repo(client: github.Github, repo_name: str, branch_name: str):
    repo = client.get_repo("Fivetran/" + repo_name)
    try:
        master_sha = repo.get_branch(branch="master").commit.sha
        default_branch = "master"
    except:
        master_sha = repo.get_branch(branch="main").commit.sha
        default_branch = "main"
    repo.create_git_ref(ref="refs/heads/" + branch_name, sha=master_sha)
    return repo, default_branch


def update_packages(
    repo: github.Repository.Repository, branch_name: str, config: dict
) -> None:
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
            message="[ci skip] Updating package dependendcies",
            content=ruamel.yaml.dump(packages, Dumper=ruamel.yaml.RoundTripDumper),
            sha=packages_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        print("'packages.yml' not found in repo.")


def update_version(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    project_content = repo.get_contents("dbt_project.yml")
    project = ruamel.yaml.load(
        project_content.decoded_content,
        Loader=ruamel.yaml.RoundTripLoader,
        preserve_quotes=True,
    )

    current_version = project["version"]
    bump_type = config["version-bump-type"]

    current_version_split = current_version.split(".")

    if bump_type == "patch":
        current_version_split[2] = str(int(current_version_split[2]) + 1)
    elif bump_type == "minor":
        current_version_split[1] = str(int(current_version_split[1]) + 1)
        current_version_split[2] = "0"
    elif bump_type == "major":
        current_version_split[0] = str(int(current_version_split[0]) + 1)
        current_version_split[1] = "0"
        current_version_split[2] = "0"

    new_version = ".".join(current_version_split)
    project["version"] = new_version

    repo.update_file(
        path=project_content.path,
        message="Updating version in dbt_project.yml",
        content=ruamel.yaml.dump(project, Dumper=ruamel.yaml.RoundTripDumper),
        sha=project_content.sha,
        branch=branch_name,
    )


def update_project(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    project_content = repo.get_contents("dbt_project.yml")
    project = ruamel.yaml.load(
        project_content.decoded_content,
        Loader=ruamel.yaml.RoundTripLoader,
        preserve_quotes=True,
    )

    project["require-dbt-version"] = config["require-dbt-version"]

    # v1.0.0 migrations

    clean_targets = project.get("clean-targets", None)
    if clean_targets:
        project["clean-targets"].append("dbt_packages")

    project.pop("source-paths", None)
    project.pop("data-paths", None)

    repo.update_file(
        path=project_content.path,
        message="[ci skip] Updating dbt_project.yml",
        content=ruamel.yaml.dump(project, Dumper=ruamel.yaml.RoundTripDumper),
        sha=project_content.sha,
        branch=branch_name,
    )


def update_integration_project(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    project_content = repo.get_contents("integration_tests/dbt_project.yml")
    project = ruamel.yaml.load(
        project_content.decoded_content,
        Loader=ruamel.yaml.RoundTripLoader,
        preserve_quotes=True,
    )

    clean_targets = project.get("clean-targets", None)
    if clean_targets:
        project["clean-targets"].append("dbt_packages")

    project.pop("source-paths", None)
    project.pop("data-paths", None)

    repo.update_file(
        path=project_content.path,
        message="[ci skip] Updating integration_tests/dbt_project.yml",
        content=ruamel.yaml.dump(project, Dumper=ruamel.yaml.RoundTripDumper),
        sha=project_content.sha,
        branch=branch_name,
    )


def update_requirements(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    try:
        requirements_content = repo.get_contents("integration_tests/requirements.txt")
        new_content = ""
        for requirement in config["requirements"]:
            new_content += f"{requirement['name']}=={requirement['version']}\n"
        repo.update_file(
            path=requirements_content.path,
            message="[ci skip] Updating dbt version in requirements.txt",
            content=new_content,
            sha=requirements_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        repo.create_file(
            path="integration_tests/requirements.txt",
            message="[ci skip] Updating dbt version in requirements.txt",
            content=new_content,
            branch=branch_name,
        )


def update_data_folder_to_seed(
    repo: github.Repository.Repository, branch_name: str
) -> None:
    try:
        seed_files = repo.get_contents("data")
    except:
        seed_files = None
    if seed_files:
        for file in seed_files:
            repo.create_file(
                path=file.path.replace("data/", "seeds/"),
                message="[ci skip] Moving folder",
                content=file.decoded_content,
                branch=branch_name,
            )
            repo.delete_file(
                path=file.path,
                message="[ci skip] Moving folder",
                sha=file.sha,
                branch=branch_name,
            )
    try:
        integration_seed_files = repo.get_contents("integration_tests/data")
    except:
        integration_seed_files = None
    if integration_seed_files:
        for file in integration_seed_files:
            repo.create_file(
                path=file.path.replace("data/", "seeds/"),
                message="[ci skip] Moving folder",
                content=file.decoded_content,
                branch=branch_name,
            )
            repo.delete_file(
                path=file.path,
                message="[ci skip] Moving folder",
                sha=file.sha,
                branch=branch_name,
            )


def add_dbt_packages_to_gitnore(
    repo: github.Repository.Repository, branch_name: str
) -> None:
    try:
        gitignore_content = repo.get_contents(".gitignore")
        gitignore = gitignore_content.decoded_content.decode("utf-8")
        gitignore += "\n"
        gitignore += "dbt_packages/"
        repo.update_file(
            path=gitignore_content.path,
            message="[ci skip] Adding dbt_packages to .gitignore",
            content=gitignore,
            sha=gitignore_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        repo.create_file(
            path=".gitignore",
            message="[ci skip] Adding dbt_packages to .gitignore",
            content="dbt_packages/",
            branch=branch_name,
        )


def open_pull_request(
    repo: github.Repository.Repository, branch_name: str, default_branch: str
) -> None:
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
        base=default_branch,
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
        repo, default_branch = setup_repo(client, repo_name, branch_name)
        update_packages(repo, branch_name, config)
        update_project(repo, branch_name, config)
        update_requirements(repo, branch_name, config)
        add_dbt_packages_to_gitnore(repo, branch_name)
        update_data_folder_to_seed(repo, branch_name)
        update_version(repo, branch_name, config)
        open_pull_request(repo, branch_name, default_branch)


if __name__ == "__main__":
    main()
