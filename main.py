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
    branch_name = 'MagicBot/' + "integation-test-webhooks-14"
    commit_message = 'testing'
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
            file_to_add='docs/' + file
            if os.path.isdir(file_to_add):
                shutil.copytree(file_to_add, path_to_repository_file)
                print (u'\u2713', "%s directory successfully added..."%(file))
            else:
                shutil.copy(file_to_add, path_to_repository_file)
                print (u'\u2713', "%s file successfully added..."%(file))
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

def add_to_file(file_paths: list, new_line: str, path_to_repository: str, insert_at_top: bool) -> None:
    for file in file_paths:
        try:
            print("Adding %s to file: %s..." %(new_line, file))
            path_to_repository_file = os.path.join(path_to_repository, file)
            
            if insert_at_top:
                with open(path_to_repository_file, 'r') as new_file:
                    content = new_file.read()
                with open(path_to_repository_file, 'w') as new_file:
                    new_file.write(new_line + '\n')
                    new_file.write(content)
                    print (u'\u2713', "%s successfully added to the top of file %s..."%(new_line, file))
            else: 
                with open(path_to_repository_file, 'a') as new_file:
                    new_file.write('\n' + new_line + '\n')
                    print (u'\u2713', "%s successfully added to the bottom of file %s..."%(new_line, file))

        except Exception as e:
            print (u'\u2717', "Adding %s file %s. Error: %s..." %(new_line, file, e))

def open_pull_request(
    repo: github.Repository.Repository, branch_name: str, default_branch: str
) -> None:
    body = """This pull request was created automatically 🎉:\n- [ ] Ensure `.buildkite/scripts/run_models.sh` has the new run-operation line\n- [ ] Update the package version (currently `v0.UPDATE.UPDATE`) in the `CHANGELOG`\n- [ ] Update project versions in the `dbt_project.yml` and `integration_tests/dbt_project.yml` files\n- [ ] Update Step 2 of the `README` to align either with this [source package example](https://github.com/fivetran/dbt_shopify_source/tree/main#step-2-install-the-package-skip-if-also-using-the-shopify-transformation-package) or this [transform package example](https://github.com/fivetran/dbt_shopify#step-2-install-the-package)
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

    ## Set to True if remote branch (or PR) already exists; False if it does not yet exist
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
        
        
        # remove_files(file_paths=files_to_remove, path_to_repository=path_to_repository)

        
        # files_to_add_to=['.buildkite/run_models.sh']
        drop_schema_command='dbt run-operation fivetran_utils.drop_schemas_automation --target "$db"'
        changelog_entry='# ' + repo_name + ' v0.UPDATE.UPDATE\n\n ## Under the Hood:\n\n- Incorporated the new `fivetran_utils.drop_schemas_automation` macro into the end of each Buildkite integration test job.\n- Updated the pull request [templates](/.github).'
        add_to_file(file_paths=['.buildkite/scripts/run_models.sh'], new_line=drop_schema_command, path_to_repository=path_to_repository, insert_at_top=False)
        add_to_file(file_paths=['CHANGELOG.md'], new_line=changelog_entry, path_to_repository=path_to_repository, insert_at_top=True)
        
        files_to_remove=['.github/pull_request_template.md']
        files_to_add=['.github/PULL_REQUEST_TEMPLATE/', '.github/pull_request_template.md']

        # '.github/PULL_REQUEST_TEMPLATE/maintainer_pull_request_template.md'
        
        remove_files(file_paths=files_to_remove, path_to_repository=path_to_repository)
        add_files(file_paths=files_to_add, path_to_repository=path_to_repository)
        # add_files(file_paths=files_to_add, path_to_repository=path_to_repository)

        # find_and_replace(file_paths, config["find-and-replace-list"], path_to_repository, cloned_repository)
        # print (u'\u2713', "Finished replacing values in files")


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

        

if __name__ == "__main__":
    main()