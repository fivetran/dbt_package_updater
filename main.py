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
    files = ["dbt_project.yml","integration_tests/dbt_project.yml"]
    for f in files:
        project_content = repo.get_contents(f)
        project = ruamel.yaml.load(
            project_content.decoded_content,
            Loader=ruamel.yaml.RoundTripLoader,
            preserve_quotes=True,
        )

        # project["require-dbt-version"] = config["require-dbt-version"]
        try:
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
                message="Updating dbt version",
                content=ruamel.yaml.dump(project, Dumper=ruamel.yaml.RoundTripDumper, width=10000),
                sha=project_content.sha,
                branch=branch_name,
            )
        except:
            print("dbt project.yml files not found.")


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
            message="Updating dbt version in requirements.txt",
            content=new_content,
            sha=requirements_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        repo.create_file(
            path="integration_tests/requirements.txt",
            message="Updating dbt version in requirements.txt",
            content=new_content,
            branch=branch_name,
        )

def get_files(
    repo: github.Repository.Repository, branch_name: str, default_branch: str, store_files: list
) -> None:
    
    repo_contents = repo.get_contents("")
    while len(repo_contents) > 1:
        file_content = repo_contents.pop(0)
        if file_content.type=='dir':
            repo_contents.extend(repo.get_contents(file_content.path))
        else :
            # print(file_content.name)
            store_files.append(file_content.name)

def replace_string(
    repo: github.Repository.Repository, branch_name: str, default_branch: str, store_files: list
) -> None:
        files = ["util_example.sql"]
        for f in files:
            project_content = repo.get_contents(f)
            # project = ruamel.yaml.load(
            #     project_content.decoded_content,
            #     Loader=ruamel.yaml.RoundTripLoader,
            #     preserve_quotes=True,
            # )

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
    file_list = []

    # Setup
    branch_name = set_branch_name()
    creds = load_credentials()
    config = load_configurations()
    client = get_github_client(creds["access_token"])
    # print(config)

    # Iterate through repos
    for repo_name in config["repositories"]:
        print(repo_name)
        repo, default_branch = setup_repo(client, repo_name, branch_name)
        get_files(repo, branch_name, config, file_list)
        # print(file_list)
        replace_string(repo, branch_name, config, file_list)
        # print(branch_name)
        # update_packages(repo, branch_name, config)
        # update_project(repo, branch_name, config)
    #     update_requirements(repo, branch_name, config)
    #     open_pull_request(repo, branch_name, default_branch)


if __name__ == "__main__":
    main()
