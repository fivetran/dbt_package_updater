# allows you to interact with GitHub repositories and other GitHub resources. It is a wrapper around the GitHub REST API, which means that it allows you to perform all of the same actions that you can perform using the GitHub web interface.
import github

#  The git module in Python provides a way to interact with git repositories. It is a wrapper around the git command line tools, and it provides a high-level API for performing common git operations,
import git

class Author:
    '''
    defining Author object. For opening PRs, we need to provide github with an "Author" with the following attributes.
    '''
    name: str
    email: str

def get_pull_request_body(file_path: str) -> str:
    '''
    Reads the content of a Markdown file and stores it as a string.

    Args:
    file_path: The path to the Markdown file.

    Returns:
    The content of the Markdown file as a string.
    '''

    with open(file_path, 'r') as f:
        body = f.read()
    return body

def open_pull_request(repo: github.Repository.Repository, branch_name: str, default_branch: str, pr_title: str) -> None:
    '''
    Creates pull request with the following body and prints the url to the command line.

    Future ideas: add other parameters to the PR a la https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request
    - can create them as drafts first
    - pull default title from set_defaults() method 
    - can we add assignees or tags?
    '''
    # body = """This pull request was created automatically 🎉:\n- [ ] Ensure `.buildkite/scripts/run_models.sh` has the new run-operation line\n- [ ] Update the package version (currently `v0.UPDATE.UPDATE`) in the `CHANGELOG`\n- [ ] Update project versions in the `dbt_project.yml` and `integration_tests/dbt_project.yml` files\n- [ ] Update Step 2 of the `README` to align either with this [source package example](https://github.com/fivetran/dbt_shopify_source/tree/main#step-2-install-the-package-skip-if-also-using-the-shopify-transformation-package) or this [transform package example](https://github.com/fivetran/dbt_shopify#step-2-install-the-package)"""
    body = get_pull_request_body('pull_request_body.md')
    pull = repo.create_pull(
        title=pr_title,
        body=body,
        head=branch_name,
        base=default_branch,
    )

    print(pull.html_url)

def checkout_branch(cloned_repository: git.Repo, branch_name: str) -> git.refs.head.Head:
    '''
    Essentially the python function version of this terminal command:
    git checkout -b <branch that may or may not exist yet>

    Arguments:
    - branch_name 
    - cloned repo
    '''
    try: 
        new_branch = cloned_repository.create_head(branch_name) # Create branch if it doesn't exist
        print ("Creating new branch: %s... " %(branch_name))
        working_branch = new_branch.checkout()
        print (u'\u2713', "New branch %s created..." %(branch_name))
        print (u'\u2713', "Checking out branch: %s..." %(branch_name))
    except:
        working_branch = cloned_repository.git.checkout(branch_name)
        print ("Branch already exists, checking out branch: %s..."%(branch_name))
    
    return working_branch

def commit_changes(cloned_repository: git.Repo, branch_name: str, commit_message: str, repository_author: Author) -> None:
    '''
    Add and commit local changes to remote.

    Args:
    - cloned_repository: where the changes were made
    - branch_name: remote branch to push to
    - commit_message
    - repo author: author of the code changes/PR-to-come.
    '''
    cloned_repository.git.add(all=True)    
    cloned_repository.index.commit(commit_message.format(branch_name), author=repository_author)
    print("Committed changes...")

def push_changes(cloned_repository: git.Repo, branch_name: str, repo_name: str, repo: github.Repository.Repository, default_branch: str, new_branch: git.refs.head.Head, pr_title: str) -> None:
    '''
    Creates a pull request if one does not exist, otherwise just pushes changes to remote. 

    WIP: this currently uses a ton of arguments that are definitely somewhat duplicative (ie separating names from entities)
    '''
    
    origin = cloned_repository.remote(name='origin')
    try:
        origin.push(new_branch)
        open_pull_request(repo, branch_name, default_branch, pr_title)
        print ("PR created for: ", repo_name)
    except: 
        origin.push(branch_name)
        print ("Committed to pre-existing PR for: ", repo_name)
    print("Pushed to remote...")