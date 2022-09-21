from multiprocessing import AuthenticationError
import github
import yaml
import ruamel.yaml
import os
import git
import json
import pathlib


class Author:
    name: str
    email: str

def set_defaults() -> str:
    branch_name = "MagicBot/" + "dbt-utils-cross-db-migration"
    commit_message = "Updates for dbt-utils to dbt-core cross-db macro migration"
    return branch_name, commit_message

def load_credentials() -> dict:
    with open("credentials.yml") as file:
        creds = yaml.load(file, Loader=yaml.FullLoader)
    return creds


def get_github_client(access_token: str) -> github.Github:
    return github.Github(access_token)


def load_configurations() -> dict:
    with open("package_manager.yml") as file:
        config = ruamel.yaml.load(file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True)        
    return config

def setup_repo(
    client: github.Github, repo_name: str, branch_name: str
) -> github.Repository.Repository:
    repo = client.get_repo("Fivetran/" + repo_name)
    try:
        default_branch = "master"
        master_sha = repo.get_branch(branch=default_branch).commit.sha
    except:
        default_branch = "main"
        master_sha = repo.get_branch(branch=default_branch).commit.sha
        default_branch = "main"
    # repo.create_git_ref(ref="refs/heads/" + branch_name, sha=master_sha)
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

def get_file_paths(repo: github.Repository.Repository) -> list:
    
    file_path_list = []
    repo_contents = repo.get_contents("")
    while len(repo_contents) > 1:
        file_in_dir = repo_contents.pop(0)
        if file_in_dir.type=='dir':
            repo_contents.extend(repo.get_contents(file_in_dir.path))
        else :
            if not file_in_dir.name.endswith('tmp.sql') and file_in_dir.name.endswith('.sql'):
                file_path_list.append(file_in_dir.path)
    return (file_path_list)

def clone_repo(gh_link: str, path_to_repository: str, ssh_key: str) -> None:
    try:
        branch = "master"
        cloned_repository = git.Repo.clone_from(gh_link, path_to_repository, branch=branch,
                                            env={"GIT_SSH_COMMAND": 'ssh -i ' + ssh_key})
    except:
        branch = "main"
        cloned_repository = git.Repo.clone_from(gh_link, path_to_repository, branch=branch,
                                env={"GIT_SSH_COMMAND": 'ssh -i ' + ssh_key})
    return cloned_repository, branch

def find_and_replace(file_paths: list, find_and_replace_list: list, path_to_repository: str, cloned_repository) -> None:
    for checked_file in file_paths:
        path_to_repository_file = os.path.join(path_to_repository, checked_file)
        repo_file = pathlib.Path(path_to_repository_file)
        if repo_file.exists():
            for texts in find_and_replace_list:
                text_to_find = "dbt_utils." + texts
                text_to_replace = "dbt." + texts
                file = open(path_to_repository_file, 'r')
                current_file_data = file.read()
                file.close()
                new_file_data = current_file_data.replace(text_to_find, text_to_replace)
                file = open(path_to_repository_file, 'w')
                file.write(new_file_data)
                file.close()
            cloned_repository.index.add(path_to_repository_file)
        else:
            print("Ignoring "+path_to_repository_file+". Not found")

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
    
    return(new_version)

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
            if "package" in package and package["package"] == 'fivetran/fivetran_utils':
                package["version"] = config['fivetran-utils-version']

        repo.update_file(
            path=packages_content.path,
            message="Updating package dependencies",
            content=ruamel.yaml.dump(packages, Dumper=ruamel.yaml.RoundTripDumper),
            sha=packages_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        print("'packages.yml' not found in repo.")

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
        title="Updates for dbt-utils to dbt-core cross-db macro migration",
        body=body,
        head=branch_name,
        base=default_branch,
    )

    print(pull.html_url)

def main():
    ## Setup
    branch_name, commit_message = set_defaults()
    creds = load_credentials()
    config = load_configurations()
    client = get_github_client(creds["access_token"])
    write_to_directory = "repositories"
    repository_author = Author 
    repository_author.name = creds["repository_author_name"]
    repository_author.email = creds["repository_author_email"]
    ssh_key = creds["ssh_key"]

    ## Iterate through repos
    for repo_name in config["repositories"]:
        ## Not sure why default branch here doesn't work
        repo, default_branch = setup_repo(client, repo_name, branch_name)
        file_paths = get_file_paths(repo)
        gh_link = "git@github.com:fivetran/" + repo_name + ".git"
        path_to_repository = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            write_to_directory + '/' + repo_name )

        cloned_repository, default_branch = clone_repo(gh_link, path_to_repository, ssh_key)
        new_branch = cloned_repository.create_head(branch_name)
        new_branch.checkout()

        # Find and Replace values in config and lump into one commit
        find_and_replace(file_paths, config["find-and-replace-list"], path_to_repository, cloned_repository)
        cloned_repository.index.commit(commit_message.format(branch_name), author=repository_author)
        origin = cloned_repository.remote(name='origin')
        origin.push(new_branch)

        update_project(repo, branch_name, config)
        update_packages(repo, branch_name, config)
        open_pull_request(repo, branch_name, default_branch)

if __name__ == "__main__":
    main()
