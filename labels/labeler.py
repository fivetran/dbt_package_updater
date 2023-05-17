import subprocess
import yaml
import ruamel.yaml
import os
import git


class Author:
    name: str
    email: str

def load_configurations() -> dict:
    with open("packages.yml") as file:
        config = ruamel.yaml.load(file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True)        
    return config

def load_credentials() -> dict:
    with open("credentials.yml") as file:
        creds = yaml.load(file, Loader=yaml.FullLoader)
    return creds

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

creds = load_credentials()
config = load_configurations()
# client = get_github_client(creds["access_token"])
write_to_directory = "repositories"
repository_author = Author 
repository_author.name = creds["repository_author_name"]
repository_author.email = creds["repository_author_email"]
ssh_key = creds["ssh_key"]

for repo_name in config["repositories"]:
    print ("Label update in progress for: ", repo_name)
    ## Not sure why default branch here doesn't work
    gh_link = "git@github.com:fivetran/" + repo_name + ".git"
    path_to_repository = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        write_to_directory + '/' + repo_name )

    cloned_repository, default_branch = clone_repo(gh_link, path_to_repository, ssh_key)

    print("Adding labels for %s" %repo_name)
    # labels = ['test_label_1'] ## will change this into a dictionary so we can get colors and descriptions
    ## Alternatively we can generate one "true set" of labels and then just clone it from repo to repo
    # for label_name in labels:
    # description = "\"this is a test description\""
    # label = "test_label_1"
    # subprocess.check_call("./create_label.sh %s %s %s" % (repo_name, label, description), shell=True)
    subprocess.check_call("./clone_labels.sh %s" % (repo_name), shell=True)


