
# The os module in Python provides a portable way of using operating system dependent functionality. It provides a number of functions for interacting with the file system, processes, and other operating system resources.
import os

#  The git module in Python provides a way to interact with git repositories. It is a wrapper around the git command line tools, and it provides a high-level API for performing common git operations,
import git

# local stuff
import local_load_lib
import repo_lib
import pull_request_lib as pr_lib

class Author:
    '''
    defining Author object
    '''
    name: str
    email: str

def main():
    ## Set up & Configurations
    branch_name, commit_message = pr_lib.set_defaults()

    ## Loads credentials from your credentials.yml file, you will need to create a file that resembles `samples.credentials.yml`
    creds = local_load_lib.load_credentials()

    ## Currently loads configurations from your package_manager.yml
    config = local_load_lib.load_configurations()

    ## The below is required for you to clone the respective repos inside your package_manager.yml
    client = repo_lib.get_github_client(creds["access_token"])

    ## This is the name of the directory pkgs will be cloned into
    write_to_directory = "repositories" 

    # Create author objects
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
    ## move to own function?
    for repo_name in config["repositories"]:
        print ("PR in progress for: ", repo_name)

        ## set everything up for github
        repo = repo_lib.setup_repo(client, repo_name, branch_name)
        file_paths =repo_lib. get_file_paths(repo)
        gh_link = "git@github.com:fivetran/" + repo_name + ".git"
        path_to_repository = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            write_to_directory + '/' + repo_name )

        cloned_repository, default_branch = repo_lib.clone_repo(gh_link, path_to_repository, ssh_key)
        
        # Essentially run `$ git checkout -b branch_name` (maybe move to pr_lib?)
        if not cloned_repository.get_branch(branch_name):
            print ("Creating new branch: %s... " %(branch_name))
            new_branch = cloned_repository.create_head(branch_name) # Create branch if it doesn't exist
            new_branch.checkout()
            print (u'\u2713', "New branch %s created..." %(branch_name))
            print (u'\u2713', "Checking out branch: %s..." %(branch_name))
        else:
            cloned_repository.git.checkout(branch_name)
            print ("Branch already exists, checking out branch: %s..."%(branch_name))
        
        ## Call the file manipulation functions here!
        
        # package_updates.remove_files(file_paths=files_to_remove, path_to_repository=path_to_repository)
        # package_updates.add_files(file_paths=files_to_add, path_to_repository=path_to_repository)
        # package_updates.add_to_file(file_paths=files_to_add_to, new_line='\n', path_to_repository=path_to_repository, insert_at_top=false)

        # add and commit our changes to remote -- maybe move to pr_lib
        cloned_repository.git.add(all=True)    
        cloned_repository.index.commit(commit_message.format(branch_name), author=repository_author)
        print("Committed changes...")
        origin = cloned_repository.remote(name='origin')
    
        if not branch_exists:
            origin.push(new_branch)
            pr_lib.open_pull_request(repo, branch_name, default_branch)
            print ("PR created for: ", repo_name)
        else: 
            origin.push(branch_name)
        print("Pushed to remote...")


if __name__ == "__main__":
    main()