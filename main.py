
# The os module in Python provides a portable way of using operating system dependent functionality. It provides a number of functions for interacting with the file system, processes, and other operating system resources.
import os
# high-level interface to the operating system's file manipulation functions. It provides a number of functions for copying, moving, deleting, and renaming files and directories.
import shutil
#  The git module in Python provides a way to interact with git repositories. It is a wrapper around the git command line tools, and it provides a high-level API for performing common git operations,
import git

# local stuff
import local_load_lib
import repo_lib
import pull_request_lib as pr_lib
import package_updates

class Author:
    '''
    defining Author object. For opening PRs, we need to provide github with an "Author" with the following attributes.
    '''
    name: str
    email: str

def main():
    ## This is the name of the directory pkgs will be cloned into. Lets clear it out if it exists from a previous run
    write_to_directory = "repositories" 
    local_load_lib.clear_working_directory(write_to_directory)

    ## Set up & Configurations

    ## Loads credentials from your credentials.yml file, you will need to create a file that resembles `samples.credentials.yml`
    creds = local_load_lib.load_credentials()

    ## Currently loads configurations from your package_manager.yml
    config = local_load_lib.load_configurations()

    ## The below is required for you to clone the respective repos inside your package_manager.yml
    client = repo_lib.get_github_client(creds["access_token"])

    # Create author object
    repository_author = Author
    ## Assigns Author object a name
    repository_author.name = creds["repository_author_name"] 
    ## Assigns Author object an email
    repository_author.email = creds["repository_author_email"] 

    ## Iterates over all repos that are currently included in `package_manager.yml`
    ## Make sure there aren't more than 10 or so packages uncommented out 
    ## maybe move to own function? 
    for repo_name in config["repositories"]:
        print ("PR in progress for: ", repo_name)

        ## set everything up for github
        repo = repo_lib.setup_repo(client, repo_name, config['branch-name'])
        file_paths = repo_lib.get_file_paths(repo)
        gh_link = "git@github.com:fivetran/" + repo_name + ".git"
        path_to_repository = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            write_to_directory + '/' + repo_name )

        # clone the repo - this returns the git cloned repo and its default branch (main vs master)
        cloned_repository, default_branch = repo_lib.clone_repo(gh_link, path_to_repository, creds["ssh_key"])
        
        # Essentially run `$ git checkout -b branch_name` (maybe move to pr_lib?)
        working_branch = pr_lib.checkout_branch(cloned_repository=cloned_repository, branch_name=config['branch-name'])

        # Apply changes to package
        package_updates.add_to_file(files_to_add_to=config['files-to-add-to'], path_to_repository=path_to_repository)
        package_updates.add_files(file_paths=config['files-to-add'], path_to_repository=path_to_repository)
        package_updates.remove_files(file_paths=config['files-to-remove'], path_to_repository=path_to_repository)
        package_updates.find_and_replace(file_paths=file_paths, find_and_replace_texts=config['find-and-replace'], path_to_repository=path_to_repository)
        package_updates.update_project(repo=repo, path_to_repository=path_to_repository, config=config)

        # Add and commit changes to branch
        pr_lib.commit_changes(cloned_repository=cloned_repository, branch_name=config['branch-name'], commit_message=config['commit-message'], repository_author=repository_author)

        # Push changes to remote and open PR if one does not already exist
        # Body of PR is configured in pull_request_body.md
        pr_lib.push_changes(cloned_repository=cloned_repository, branch_name=config['branch-name'], repo_name=repo_name, repo=repo, default_branch=default_branch, new_branch=working_branch, pr_title=config['pull-request-title'])


if __name__ == "__main__":
    main()