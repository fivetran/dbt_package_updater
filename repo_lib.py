
# provides a way to create and manage multiple processes, and communicate between processes
# Processes are separate instances of the Python interpreter, and they can run concurrently on the same machine. This can be useful for tasks that can be divided into smaller pieces that can be executed in parallel, or for tasks that require a lot of processing power.

# The AuthenticationError exception is raised when a process tries to access a shared resource that it is not authorized to access.
from multiprocessing import AuthenticationError

# allows you to interact with GitHub repositories and other GitHub resources. It is a wrapper around the GitHub REST API, which means that it allows you to perform all of the same actions that you can perform using the GitHub web interface.
import github

# allows you to read, write, and parse YAML files
import yaml

# ruamel.yaml is a YAML 1.2 loader/dumper package for Python. It is a fork of the PyYAML library
# powerful and flexible YAML parser that can be used for a variety of tasks. It is a good choice for applications that require a high degree of control over the YAML format.
import ruamel.yaml

#  The git module in Python provides a way to interact with git repositories. It is a wrapper around the git command line tools, and it provides a high-level API for performing common git operations,
import git

def get_github_client(access_token: str) -> github.Github:
    '''
    Args: 
    - access_token from credentials yaml, see README instructions
    
    Returns:
    - Github client (an integrated development environment)
    '''
    return github.Github(access_token)


def setup_repo(client: github.Github, repo_name: str, branch_name: str) -> github.Repository.Repository:
    '''
    returns the github repo so we can interact with it

    Args:
    - Github client (from get_github_client())
    - repo name
    - branch name (from set_default())

    Returns:
    - Github repo object
    '''
    repo = client.get_repo("Fivetran/" + repo_name)
    return repo

def clone_repo(gh_link: str, path_to_repository: str, ssh_key: str) -> None:
    ''' 
    creates (but doesn't return) a cloned repo -> this will get put in the root/repositories/ folder

    Args:
    - github repo link
    - path to repostiory
    - ssh key you created (see README Credential instructions)
    '''
    try:
        default_branch = "master"
        cloned_repository = git.Repo.clone_from(gh_link, path_to_repository, branch=default_branch,
                                            env={"GIT_SSH_COMMAND": 'ssh -i ' + ssh_key})
    except:
        default_branch = "main"
        cloned_repository = git.Repo.clone_from(gh_link, path_to_repository, branch=default_branch,
                                env={"GIT_SSH_COMMAND": 'ssh -i ' + ssh_key})
    return cloned_repository, default_branch

def get_file_paths(repo: github.Repository.Repository) -> list:
    '''
    takes GitHub repository object as input and returns a list of file paths in the repository that
    meet the requirements in the last `if` statement of this function

    Args:
    - github repo object from setup_repo()

    Returns:
    - list of file paths in the repo 
    '''
    file_path_list = []
    repo_contents = repo.get_contents("") # "" as the `path` loads the contents of the root directory
    while len(repo_contents) > 1:
        file_in_dir = repo_contents.pop(0) # removes the file at the top of the list and returns the removed item
        if file_in_dir.type=='dir':
            # recursively flatten folders and add contents to repo_contents
            repo_contents.extend(repo.get_contents(file_in_dir.path))
        else: 
            # don't include _tmp models, packages.yml, or buildkite creds
            # DO include only sql and yml files - update_pre_run
            if not file_in_dir.name.endswith('tmp.sql') and \
                not file_in_dir.name.endswith('sample.profiles.yml') and \
                not file_in_dir.name.endswith('packages.yml') and \
                (file_in_dir.name.endswith('.sql') or file_in_dir.name.endswith('.yml')):
                file_path_list.append(file_in_dir.path)
    return (file_path_list)