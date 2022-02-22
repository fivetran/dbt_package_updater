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
        files = ['pull_request_template.md','ISSUE_TEMPLATE/bug-report.yml','ISSUE_TEMPLATE/feature-request.yml','ISSUE_TEMPLATE/config.yml'] # These can be updated for the files and path you want to upload
        
        for file in files:
            ## Previous templates had a different file names, next time, maybe there is a replace_file function instead?
            old_content = repo.get_contents(".github/" + file) 
            repo.delete_file(".github/" + file, "deleting old files", old_content.sha, branch=branch_name) ## delete previous file

            current_file = open('docs/' + file, 'r')
            content = current_file.read()
            repo.create_file(".github/" + file, "template add", content, branch=branch_name) # This make three concurrent commits, maybe there is a way to have it wait?

    except github.GithubException as error:
        print("The creation of the templates failed")

def open_pull_request(repo: github.Repository.Repository, branch_name: str, default_branch) -> None:
    body = """
    ---
    assignees: 'fivetran-sheringuyen'
    ---
    This pull request was created automatically 🎉
    This PR does not require cutting a release as it only includes cosmetic changes by including Issue and PR templates which do not
    impact the contents of the package.

    Before merging this PR:
    - [ ] Verify that all the tests pass.
    """

    try:
        pull = repo.create_pull(
            title="[MagicBot] - Updating Issue templates",
            body=body,
            head=branch_name,
            base="master"
        )
    except:
        pull = repo.create_pull(
            title="[MagicBot] - Updating Issue templates",
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
        print (repo_name)
        repo, default_branch = setup_repo(client, repo_name, branch_name)
        # print ("REPO:", repo, "\n DEFAULT BRANCH:", default_branch)
        update_packages(repo, branch_name, config)
        open_pull_request(repo, branch_name, default_branch)

if __name__=="__main__":
    main()