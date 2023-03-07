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
    branch_name = 'MagicBot/' + "fill-in-name-here"
    commit_message = 'fill in commit msg'
    return branch_name, commit_message

def load_credentials() -> dict:
    with open("credentials.yml") as file:
        creds = yaml.load(file, Loader=yaml.FullLoader)
    return creds

def get_github_client(access_token: str) -> github.Github:
    return github.Github(access_token)

def load_configurations() -> dict:
    """
    Loads configurations from `package_manager.yml` file located in root repo
    """
    with open("package_manager.yml") as file:
        config = ruamel.yaml.load(file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True)        
    return config

def setup_repo(
    client: github.Github, repo_name: str, branch_name: str
) -> github.Repository.Repository:
    repo = client.get_repo("Fivetran/" + repo_name)
    return repo

def clone_repo(gh_link: str, path_to_repository: str, ssh_key: str) -> None:
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

def remove_files(file_paths: list, path_to_repository: str) -> None:
    for file in file_paths: 
        try:
            print ("Removing file: %s..." %(file))
            path_to_repository_file = os.path.join(path_to_repository, file)
            os.remove(path_to_repository_file)
            print (u'\u2713',"File: %s successfully removed..."%(file))
        except Exception as e:
            print (u'\u2717', "Removing file %s FAILED. Error: %s..." %(file, e))

def add_files(file_paths: list, path_to_repository: str) -> None:
    for file in file_paths:
        try:
            print("Adding file: %s..." %(file))
            path_to_repository_file = os.path.join(path_to_repository, file)
            file_to_add='docs/'+file
            shutil.copy(file_to_add, path_to_repository_file)
            print (u'\u2713', "%s successfully added..."%(file))
        except Exception as e:
            print (u'\u2717', "Adding file %s. Error: %s..." %(file, e))

def find_and_replace(file_paths: list, find_and_replace_list: list, path_to_repository: str, cloned_repository) -> None:
    num_files_to_update=len(file_paths)
    num_current_file=0
    for checked_file in file_paths:
        num_current_file+=1
        print ("Files find and replaced: " , num_current_file , "/", num_files_to_update)
        path_to_repository_file = os.path.join(path_to_repository, checked_file)
        repo_file = pathlib.Path(path_to_repository_file)
        if repo_file.exists():
            for texts in find_and_replace_list:
                text_to_find = "dbt_utils." + texts
                text_to_replace = "dbt." + texts
                if text_to_find == "dbt_utils.surrogate_key":
                    text_to_replace = "dbt_utils.generate_surrogate_key"
                if text_to_find == "dbt_utils.current_timestamp" or text_to_find == "dbt_utils.current_timestamp_in_utc":
                    ## This is because current_timestamp exists as a subtext of current_timestamp_in_utc so we'll have incorrect find and replacing
                    text_to_find = text_to_find+"("
                    text_to_replace = text_to_replace+"_backcompat"+"("
                if texts == "spark":
                    text_to_find = "spark"
                    text_to_replace = "!!!!!!! REPLACE 'spark' WITH 'spark','databricks' OR EQUIV !!!!!!!"
                file = open(path_to_repository_file, 'r')
                current_file_data = file.read()
                file.close()
                new_file_data = current_file_data.replace(text_to_find, text_to_replace)
                file = open(path_to_repository_file, 'w')
                file.write(new_file_data)
                file.close()
        else:
            print("Ignoring "+path_to_repository_file+". Not found")

def open_pull_request(
    repo: github.Repository.Repository, branch_name: str, default_branch: str
) -> None:
    body = """This pull request was created automatically 🎉\nBefore merging this PR (refer to Detailed Update Sheet 10/2022 for more information):\n- [ ] Verify `dbt_project.yml` & `integration_tests/dbt_project.yml` versions are properly bumped\n- [ ] Spot check for dispatch updates, `dbt_utils.macro` -> `dbt.macro` \n- [ ] Verify that `.circleci` directory has been removed\n- [ ] Verify `integration_tests/requirements.txt` adapters have been updated to 1.2.0 and dbt-databricks is added\n- [ ] Verify `.buildkite` directory has been added with the following: `hooks/pre-command`, `scripts/run_models.sh`, `pipeline.yml`\n- [ ] Update `packages.yml`, will need to bump source package (FT utils should be bumped)\n- [ ] Update `.buildkite/scripts/run_models.sh` with vars as applicable, if N/A then remove relevant lines from script\n- [ ] Remove databricks block from `.buildkite/pipeline.yml` if package is incompatible\n- [ ] Update schema names in `integration_tests/ci/sample.profiles.yml`\n- [ ] Update "spark" strings where applicable\n- [ ] Update `CHANGELOG` [template](https://github.com/fivetran/dbt_package_updater/blob/update/dbt-utils-crossdb-migration/CHANGELOG.md) and remove surrogate keys if not applicable to package\n- [ ] Update `README` for dbt version badge, install package version range and dependencies for: Fivetran_utils, dbt-utils and source packages\n- [ ] Regenerate docs\n- [ ] Follow Instructions for adding Buildkite \n- [ ] Follow instructions for removing Circleci
    """

    pull = repo.create_pull(
        title="Package Updater Testing PR",
        body=body,
        head=branch_name,
        base=default_branch,
    )

    print(pull.html_url)

def update_project(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    '''
    SCRIPT NEEDS TO BE UDPATED
    '''
    files = ["dbt_project.yml","integration_tests/dbt_project.yml"]
    for f in files:
        project_content = repo.get_contents(f)
        project = ruamel.yaml.load(
            project_content.decoded_content,
            Loader=ruamel.yaml.RoundTripLoader,
            preserve_quotes=True,
        )

        if f == "dbt_project.yml":
            project["require-dbt-version"] = config["require-dbt-version"]

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
        except github.GithubException as error:
            print("dbt project.yml files not found.")
            # print("error: ", error)

def update_packages(
    repo: github.Repository.Repository, branch_name: str, config: dict
) -> None:
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

    write_to_directory = "repositories" ## This is the name of the directory pkgs will be cloned into
    repository_author = Author ## Creates an Author object
    repository_author.name = creds["repository_author_name"] ## Assigns Author object a name
    repository_author.email = creds["repository_author_email"] ## Assigns Author object an email
    ssh_key = creds["ssh_key"]

    ## Set to True if remote branch already exists; False if it does not yet exist
    branch_exists = False

    ## Iterates over all repos that are currently included in `package_manager.yml`
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
        
        files_to_remove=['integration_tests/requirements.txt']
        remove_files(file_paths=files_to_remove, path_to_repository=path_to_repository)

        files_to_add=['integration_tests/requirements2.txt']
        add_files(file_paths=files_to_add, path_to_repository=path_to_repository)

        find_and_replace(file_paths, config["find-and-replace-list"], path_to_repository, cloned_repository)
        print (u'\u2713', "Finished replacing values in files")


        cloned_repository.git.add(all=True)    
        cloned_repository.index.commit(commit_message.format(branch_name), author=repository_author)
        print("Committed changes...")
        origin = cloned_repository.remote(name='origin')
    
        if not branch_exists:
            origin.push(new_branch)
        else: 
            origin.push(branch_name)
        print("Pushed to remote...")

        ## The following two try statements will need to be updated once their functions are updated and made sure to successfully run across all instances
        # try:
        #     update_project(repo, branch_name, config)
        #     print("Updated project versions...")
        # except: 
        #     print("Updating project versions FAILED...")

        # try:
        #     update_packages(repo, branch_name, config)
        #     print("Updated package versions...")
        # except:
        #     print("Updating packages FAILED...")

        open_pull_request(repo, branch_name, default_branch)
        print ("PR created for: ", repo_name)

if __name__ == "__main__":
    main()