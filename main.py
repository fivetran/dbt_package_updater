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
        config = ruamel.yaml.load(file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True)        
    return config


def setup_repo(
    client: github.Github, repo_name: str, branch_name: str
) -> github.Repository.Repository:
    repo = client.get_repo("Fivetran/" + repo_name)
    try:
        master_sha = repo.get_branch(branch="master").commit.sha
    except:
        master_sha = repo.get_branch(branch="main").commit.sha
    repo.create_git_ref(ref="refs/heads/" + branch_name, sha=master_sha)
    return repo


def update_packages(
    repo: github.Repository.Repository, branch_name: str, config: dict
) -> None:
    try:
        files = ['pull_request_template.md','ISSUE_TEMPLATE/bug_report.md','ISSUE_TEMPLATE/feature_request.md','ISSUE_TEMPLATE/question.md'] # These can be updated for the files and path you want to upload
        for file in files:
            current_file = open('docs/' + file, 'r')
            content = current_file.read()
            repo.create_file(".github/" + file, "template add", content, branch=branch_name) # This make three concurrent commits, maybe there is a way to have it wait?
    except github.GithubException:
        print("The creation of the templates failed")

def open_pull_request(repo: github.Repository.Repository, branch_name: str) -> None:
    body = """
    ---
    assignees: 'fivetran-joemarkiewicz'
    ---
    This pull request was created automatically 🎉
    This PR does not require cutting a release as it only includes cosmetic changes by including Issue and PR templates which do not
    impact the contents of the package.

    Before merging this PR:
    - [ ] Verify that all the tests pass.
    """
    try:
        pull = repo.create_pull(
            title="[MagicBot] - Adding Issue and PR templates",
            body=body,
            head=branch_name,
            base="master"
        )
    except:
        pull = repo.create_pull(
            title="[MagicBot] - Adding Issue and PR templates",
            body=body,
            head=branch_name,
            base="main"
        )

    print(pull.html_url)

def main():
    # Setup
    branch_name = set_branch_name()
    creds = load_credentials()
    config = load_configurations()
    client = get_github_client(creds["access_token"])

    # Iterate through repos
    for repo_name in config["repositories"]:
        print(repo_name)
        repo = setup_repo(client, repo_name, branch_name)
        update_packages(repo, branch_name, config)
        open_pull_request(repo, branch_name)


if __name__ == "__main__":
    main()
