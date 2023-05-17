from multiprocessing import AuthenticationError
# provides a way to create and manage multiple processes, and communicate between processes
# Processes are separate instances of the Python interpreter, and they can run concurrently on the same machine. This can be useful for tasks that can be divided into smaller pieces that can be executed in parallel, or for tasks that require a lot of processing power.

# The AuthenticationError exception is raised when a process tries to access a shared resource that it is not authorized to access.

import github
# allows you to interact with GitHub repositories and other GitHub resources. It is a wrapper around the GitHub REST API, which means that it allows you to perform all of the same actions that you can perform using the GitHub web interface.

import yaml
# allows you to read, write, and parse YAML files

import ruamel.yaml
# ruamel.yaml is a YAML 1.2 loader/dumper package for Python. It is a fork of the PyYAML library
# powerful and flexible YAML parser that can be used for a variety of tasks. It is a good choice for applications that require a high degree of control over the YAML format.

import os
# The os module in Python provides a portable way of using operating system dependent functionality. It provides a number of functions for interacting with the file system, processes, and other operating system resources.

import git
#  The git module in Python provides a way to interact with git repositories. It is a wrapper around the git command line tools, and it provides a high-level API for performing common git operations,

import json
# The json module in Python provides a way to read, write, and parse JSON data.

import pathlib
# The pathlib module in Python provides a way to work with file paths in a more object-oriented way (requires python >= 3.4)

import shutil
# high-level interface to the operating system's file manipulation functions. It provides a number of functions for copying, moving, deleting, and renaming files and directories.

from datetime import datetime
# provides a number of classes and functions for representing and manipulating dates and times, as well as for formatting and parsing dates and times in a variety of formats.

class Author:
    '''
    defining Author object
    '''
    name: str
    email: str

def set_defaults() -> str:
    '''
    set Branch name and commit messsage.
    Note that the branch_exists var is set in main() - make sure that if it's set to false, there is not branch with this name in the repo 
    
    Future: should this also set the default PR title? Should the default PR title = commit message?
    '''
    branch_name = 'MagicBot/' + "rollout-mass-updates" # update_pre_run
    commit_message = 'Mass package update rollout ' + datetime.today().year + '-' + datetime.today.month
    return branch_name, commit_message

def load_credentials() -> dict:
    '''
    load the credentials you created in the prerequisites for using this package:
    - username
    - ssh key
    - access token 
    - repository_author_name
    - repository_author_email
    '''
    with open("credentials.yml") as file:
        creds = yaml.load(file, Loader=yaml.FullLoader)
    return creds

def get_github_client(access_token: str) -> github.Github:
    '''
    Args: 
    - access_token from credentials yaml, see README instruction
    
    Returns:
    - Github client (an integrated development environment)
    '''
    return github.Github(access_token)

def load_configurations() -> dict:
    """
    Loads all configurations from `package_manager.yml` file located in root repo
    
    Returns:
    - dictionary object of configurations that were defined in yml
    """
    with open("package_manager.yml") as file:
        config = ruamel.yaml.load(file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True)        
    return config

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

def remove_files(file_paths: list, path_to_repository: str) -> None:
    '''
    given a list of file paths and a git repo, remove the files from the repo.

    Args:
    - file paths to remove 
    - repo pathway 
    '''
    for file in file_paths: 
        try:
            print ("Removing file: %s..." %(file))
            path_to_repository_file = os.path.join(path_to_repository, file) # returns path_to_repository/file_path/../file.sql
            os.remove(path_to_repository_file)
            print (u'\u2713',"File: %s successfully removed..."%(file))
        except Exception as e:
            print (u'\u2717', "Removing file %s FAILED. Error: %s..." %(file, e))

def add_files(file_paths: list, path_to_repository: str) -> None:
    '''
    given a list of file paths and a git repo, add the files to from the repo. 
    The file paths should map onto file paths inside of the `docs/` folder of this package.
    doesn't return anything
    '''
    for file in file_paths:
        try:
            print("Adding file: %s..." %(file))
            path_to_repository_file = os.path.join(path_to_repository, file) # returns path_to_repository/file_path/../file.sql
            file_to_add='docs/' + file # the files to add should be stored in the docs folder
            if os.path.isdir(file_to_add):
                shutil.copytree(file_to_add, path_to_repository_file) # FYI copytee also has an optional `ignore` list argument if so needed
                print (u'\u2713', "%s directory successfully added..."%(file))
            else:
                shutil.copy(file_to_add, path_to_repository_file)
                print (u'\u2713', "%s file successfully added..."%(file))
        except Exception as e:
            print (u'\u2717', "Adding file %s. Error: %s..." %(file, e))

def find_and_replace(file_paths: list, find_and_replace_list: list, path_to_repository: str) -> None:
    '''
    find and replace text in given file paths.

    Future idea: turn `find_and_replace_list` into `find_and_replace_dict`
    '''
    num_files_to_update=len(file_paths)
    num_current_file=0
    for checked_file in file_paths:
        num_current_file+=1
        print ("Files find-and-replaced: " , num_current_file , "/", num_files_to_update)
        path_to_repository_file = os.path.join(path_to_repository, checked_file)
        repo_file = pathlib.Path(path_to_repository_file)
        if repo_file.exists():
            for texts in find_and_replace_list:
                # this code is for changing the alias of stuff
                text_to_find = "dbt_utils." + texts
                text_to_replace = "dbt." + texts
                if text_to_find == "dbt_utils.surrogate_key":
                    text_to_replace = "dbt_utils.generate_surrogate_key"
                file = open(path_to_repository_file, 'r') # open the file for reading
                current_file_data = file.read() # load in the file content
                file.close() # close the file
                new_file_data = current_file_data.replace(text_to_find, text_to_replace) # replace strings
                file = open(path_to_repository_file, 'w') # reopen the file for writing
                file.write(new_file_data) # overwrite the file
                file.close() # close the file
        else:
            print("Ignoring "+path_to_repository_file+". Not found")

def add_to_file(file_paths: list, new_line: str, path_to_repository: str, insert_at_top: bool) -> None:
    '''
    takes file paths and adds a new line either at the top or end of each file. 
    '''
    for file in file_paths:
        try:
            print("Adding %s to file: %s..." %(new_line, file))
            path_to_repository_file = os.path.join(path_to_repository, file)
            
            if insert_at_top:
                with open(path_to_repository_file, 'r') as new_file: # read in the file
                    content = new_file.read() # load in file
                with open(path_to_repository_file, 'w') as new_file: # read in the file but we'll write to it
                    new_file.write(new_line + '\n') # start the file with the new line(s)
                    new_file.write(content) # write the rest of the file
                    print (u'\u2713', "%s successfully added to the top of file %s..."%(new_line, file))
            else: 
                with open(path_to_repository_file, 'a') as new_file: # open file for appending
                    new_file.write('\n' + new_line + '\n') # write to end of file
                    print (u'\u2713', "%s successfully added to the bottom of file %s..."%(new_line, file))

        except Exception as e:
            print (u'\u2717', "Adding %s file %s. Error: %s..." %(new_line, file, e))

def open_pull_request(repo: github.Repository.Repository, branch_name: str, default_branch: str) -> None:
    '''
    Creates pull request with the following body and prints the url to the command line.

    Future ideas: add other parameters to the PR a la https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request
    - can create them as drafts first
    - pull default title from set_defaults() method 
    - can we add assignees or tags?
    '''
    body = """This pull request was created automatically 🎉:\n- [ ] Ensure `.buildkite/scripts/run_models.sh` has the new run-operation line\n- [ ] Update the package version (currently `v0.UPDATE.UPDATE`) in the `CHANGELOG`\n- [ ] Update project versions in the `dbt_project.yml` and `integration_tests/dbt_project.yml` files\n- [ ] Update Step 2 of the `README` to align either with this [source package example](https://github.com/fivetran/dbt_shopify_source/tree/main#step-2-install-the-package-skip-if-also-using-the-shopify-transformation-package) or this [transform package example](https://github.com/fivetran/dbt_shopify#step-2-install-the-package)"""
    
    pull = repo.create_pull(
        title="Package Updater PR", # update_pre_run
        body=body,
        head=branch_name,
        base=default_branch,
    )

    print(pull.html_url)

def update_project(repo: github.Repository.Repository, branch_name: str, config: str) -> None:
    '''
    WIP: currently does not work consistently enough. Did not work in last rollout for 1/2 of packages

    Intention is to update all `dbt_project.yml` (root project and /integration_tests) for a major.minor.patch version bump
    '''
    files = ["dbt_project.yml","integration_tests/dbt_project.yml"]
    for f in files:
        project_content = repo.get_contents(f)
        project = ruamel.yaml.load(
            project_content.decoded_content, # decoded_content is in bytes? perhaps stream should = contents
            Loader=ruamel.yaml.RoundTripLoader, # RoundTripLoader in ruamel.yaml is a loader that preserves the structure of the YAML document when loading it into a Python object. This means that the order of the keys in a dictionary, the order of the items in a list, and the nesting of objects will be preserved when the YAML document is loaded.
            preserve_quotes=True
        )

        if f == "dbt_project.yml":
            project["require-dbt-version"] = config["require-dbt-version"]

        try:
            current_version = project["version"]
            bump_type = config["version-bump-type"] # perhaps this should be a function argument?
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
            old_version = project["version"]
            project["version"] = new_version

            repo.update_file(
                path=project_content.path,
                message="Updating dbt version from " + old_version + " to " + project["version"],
                content=ruamel.yaml.dump(project, Dumper=ruamel.yaml.RoundTripDumper, width=10000),
                sha=project_content.sha,
                branch=branch_name,
            )
        except github.GithubException as error:
            print("dbt project.yml files not found. Error: %s" %(error))

def update_packages(repo: github.Repository.Repository, branch_name: str, config: dict) -> None:
    '''
    SCRIPT NEEDS TO BE UDPATED
    '''
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

def main():
    ## Set up & Configurations
    branch_name, commit_message = set_defaults()

    ## Loads credentials from your credentials.yml file, you will need to create a file that resembles `samples.credentials.yml`
    creds = load_credentials()

    ## Currently loads configurations from your package_manager.yml
    config = load_configurations()

    ## The below is required for you to clone the respective repos inside your package_manager.yml
    client = get_github_client(creds["access_token"])

    ## This is the name of the directory pkgs will be cloned into
    write_to_directory = "repositories" 

    # Create author object
    repository_author = Author
    ## Assigns Author object a name
    repository_author.name = creds["repository_author_name"] 
    ## Assigns Author object an email
    repository_author.email = creds["repository_author_email"] 
    ## Store the ssh key from our credentials.yml
    ssh_key = creds["ssh_key"]

    ## Set to True if remote branch (or PR) already exists; False if it does not yet exist
    branch_exists = False # update_pre_run

    ## Iterates over all repos that are currently included in `package_manager.yml`
    ## Make sure there aren't more than 10 or so packages uncommented out 
    for repo_name in config["repositories"]:
        print ("PR in progress for: ", repo_name)

        repo = setup_repo(client, repo_name, branch_name)
        file_paths = get_file_paths(repo)
        gh_link = "git@github.com:fivetran/" + repo_name + ".git"
        path_to_repository = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            write_to_directory + '/' + repo_name )

        cloned_repository, default_branch = clone_repo(gh_link, path_to_repository, ssh_key)
        if not branch_exists:
            print ("Creating new branch: %s... " %(branch_name))
            new_branch = cloned_repository.create_head(branch_name)
            new_branch.checkout()
            print (u'\u2713', "New branch %s created..." %(branch_name))
            print (u'\u2713', "Checking out branch: %s..." %(branch_name))
        else:
            cloned_repository.git.checkout(branch_name)
            print ("Branch already exists, checking out branch: %s..."%(branch_name))
        
        ## Call the file manipulation functions here!
        
        # remove_files(file_paths=files_to_remove, path_to_repository=path_to_repository)
        # add_files(file_paths=files_to_add, path_to_repository=path_to_repository)
        # add_to_file(file_paths=files_to_add_to, new_line='\n', path_to_repository=path_to_repository, insert_at_top=false)

        # add and commit our changes to remote
        cloned_repository.git.add(all=True)    
        cloned_repository.index.commit(commit_message.format(branch_name), author=repository_author)
        print("Committed changes...")
        origin = cloned_repository.remote(name='origin')
    
        if not branch_exists:
            origin.push(new_branch)
            open_pull_request(repo, branch_name, default_branch)
            print ("PR created for: ", repo_name)
        else: 
            origin.push(branch_name)
        print("Pushed to remote...")


if __name__ == "__main__":
    main()