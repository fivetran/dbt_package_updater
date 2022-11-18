from multiprocessing import AuthenticationError
import github
import yaml
import ruamel.yaml
import os
import git
import json
import pathlib
import shutil


class Author:
    name: str
    email: str

def set_defaults() -> str:
    branch_name = "MagicBot/" + "dbt-utils-cross-db-migration"
    commit_message = "Update pipeline, CI refs, run models"
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
            if not file_in_dir.name.endswith('tmp.sql') and \
                not file_in_dir.name.endswith('config.yml') and \
                not file_in_dir.name.endswith('sample.profiles.yml') and \
                not file_in_dir.name.endswith('packages.yml') and \
                (file_in_dir.name.endswith('.sql') or file_in_dir.name.endswith('.yml')):
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

def find_and_replace(file_paths: list, find_and_replace_list: dict, path_to_repository: str, cloned_repository) -> None:
    for checked_file in file_paths:
        print ("Files to update: ", checked_file)
        path_to_repository_file = os.path.join(path_to_repository, checked_file)
        repo_file = pathlib.Path(path_to_repository_file)
        if repo_file.exists():
            text_to_find = find_and_replace_list['find']
            text_to_replace = find_and_replace_list['replace']
            if checked_file.endswith('.md'):
                file = open(path_to_repository_file, 'r', encoding='utf8') 
            else:
                file = open(path_to_repository_file, 'r')
            current_file_data = file.read()
            file.close()
            new_file_data = current_file_data.replace(text_to_find, text_to_replace)
            if checked_file.endswith('.md'):
                file = open(path_to_repository_file, 'w', encoding='utf8')
            else:
                file = open(path_to_repository_file, 'w')
            file.write(new_file_data)
            file.close()
            cloned_repository.index.add(path_to_repository_file)
        else:
            print("Ignoring "+path_to_repository_file+". Not found")

def replace_files(file_paths: list, path_to_repository: str, cloned_repository) -> None:
    for checked_file in file_paths:
        print ("Files to update: ", checked_file)
        path_to_repository_file = os.path.join(path_to_repository, checked_file)
        path_to_repository_file_placeholder = path_to_repository_file.replace('pull_request_template', 'original_pull_request_template')
        os.rename(path_to_repository_file, path_to_repository_file_placeholder)
        file_to_copy='docs/.github/pull_request_template.md'
        shutil.copy(file_to_copy, path_to_repository_file)
        os.remove(path_to_repository_file_placeholder)
        cloned_repository.index.add(path_to_repository_file)

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
        print ("PR update in progress for: ", repo_name)
        ## Not sure why default branch here doesn't work
        repo, default_branch = setup_repo(client, repo_name, branch_name)
        gh_link = "git@github.com:fivetran/" + repo_name + ".git"
        path_to_repository = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            write_to_directory + '/' + repo_name )

        cloned_repository, default_branch = clone_repo(gh_link, path_to_repository, ssh_key)

        ## checkout on current PR working repo
        cloned_repository.git.checkout(branch_name)

        pipeline = ['.buildkite/pipeline.yml']
        find_and_replace_list = {'find': ':upside_down_face:', 'replace': ':bricks:'}
        find_and_replace(file_paths=pipeline, \
            find_and_replace_list=find_and_replace_list, \
                path_to_repository=path_to_repository, \
                cloned_repository=cloned_repository)
        
        sample_profs = ['integration_tests/ci/sample.profiles.yml']
        find_and_replace_list = {'find': 'CircleCI', 'replace': 'Buildkite'}
        find_and_replace(file_paths=sample_profs, \
            find_and_replace_list=find_and_replace_list, \
                path_to_repository=path_to_repository, \
                cloned_repository=cloned_repository)
        
        pr_template = ['.github/pull_request_template.md']
        replace_files(file_paths=pr_template, \
                path_to_repository=path_to_repository, \
                cloned_repository=cloned_repository)

        run_models = ['.buildkite/scripts/run_models.sh']
        find_and_replace_list = {'find': 'apt-get update', 'replace': 'set -euo pipefail\n\napt-get update'}
        find_and_replace(file_paths=run_models, \
            find_and_replace_list=find_and_replace_list, \
                path_to_repository=path_to_repository, \
                cloned_repository=cloned_repository)

        print("Finished replacing values in files...")
        cloned_repository.index.commit(commit_message.format(branch_name), author=repository_author)
        print("Committed changes...")
        origin = cloned_repository.remote(name='origin')
        origin.push(branch_name)
        print("Pushed to remote...")

if __name__ == "__main__":
    main()
