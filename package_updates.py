# The os module in Python provides a portable way of using operating system dependent functionality. It provides a number of functions for interacting with the file system, processes, and other operating system resources.
import os

# high-level interface to the operating system's file manipulation functions. It provides a number of functions for copying, moving, deleting, and renaming files and directories.
import shutil

# The pathlib module in Python provides a way to work with file paths in a more object-oriented way (requires python >= 3.4)
import pathlib

# allows you to interact with GitHub repositories and other GitHub resources. It is a wrapper around the GitHub REST API, which means that it allows you to perform all of the same actions that you can perform using the GitHub web interface.
import github

# ruamel.yaml is a YAML 1.2 loader/dumper package for Python. It is a fork of the PyYAML library
# powerful and flexible YAML parser that can be used for a variety of tasks. It is a good choice for applications that require a high degree of control over the YAML format.
import ruamel.yaml

# regex
import re

def remove_files(file_paths: list, path_to_repository: str) -> None:
    '''
    given a list of file paths and a git repo, remove the files from the repo.

    Args:
    - file paths to remove 
    - cloned repo pathway 
    '''
    for file in file_paths: 
        try:
            print ("Removing file: %s..." %(file))
            path_to_repository_file = os.path.join(path_to_repository, file) # returns path_to_repository/file_path/../file.sql
            if os.path.isdir(path_to_repository_file):
                shutil.rmtree(path_to_repository_file)
                print (u'\u2713',"Folder: %s successfully removed..."%(file))
            else:
                os.remove(path_to_repository_file)
                print (u'\u2713',"File: %s successfully removed..."%(file))
        except Exception as e:
            print (u'\u2717', "Removing file %s FAILED. Error: %s..." %(file, e))

def add_files(file_paths: list, path_to_repository: str, files_to_add_directory='files_to_add') -> None:
    '''
    given a list of file paths and a git repo, add the files to from the repo. 
    The file paths should map onto file paths inside of the `files_to_add/` folder of this package.
    doesn't return anything

    Args:
    - file paths: files to add (within their directory `files_to_add_directory`)
    - path_to_repository: cloned repo
    - files_to_add_directory = default is 'files_to_add' but can be overwritten
    '''
    for file in file_paths:
        try:
            print("Adding file: %s..." %(file))
            path_to_repository_file = os.path.join(path_to_repository, file) # returns path_to_repository/file_path/../file.sql
            file_to_add=files_to_add_directory + '/' + file # the files to add should be stored in the docs folder
            if os.path.isdir(file_to_add):
                shutil.copytree(file_to_add, path_to_repository_file) # FYI copytee also has an optional `ignore` list argument if so needed
                print (u'\u2713', "%s directory successfully added..."%(file))
            else:
                shutil.copy(file_to_add, path_to_repository_file)
                print (u'\u2713', "%s file successfully added..."%(file))
        except Exception as e:
            print (u'\u2717', "Adding file %s. Error: %s..." %(file, e))

def find_and_replace(file_paths: list, find_and_replace_texts: list, path_to_repository: str) -> None:
    '''
    find and replaces instances of text in the files of a repo

    Args:
    - file_paths: the repo files to be adjusted
    - find_and_replace_texts: list configured in package_manager.yml 
    - path_to_repository: the path to the cloned repo
    '''
    num_files_to_update=len(file_paths)
    num_current_file=0
    for checked_file in file_paths:
        num_current_file+=1
        print ("Files find-and-replaced: " , num_current_file , "/", num_files_to_update)
        path_to_repository_file = os.path.join(path_to_repository, checked_file)
        repo_file = pathlib.Path(path_to_repository_file)
        if repo_file.exists():
            for texts in find_and_replace_texts:
                file = open(path_to_repository_file, 'r') # open the file for reading
                current_file_data = file.read() # load in the file content
                file.close() # close the file
                new_file_data = current_file_data.replace(texts['find'], texts['replace']) # replace strings
                file = open(path_to_repository_file, 'w') # reopen the file for writing
                file.write(new_file_data) # overwrite the file
                file.close() # close the file
        else:
            print("Ignoring "+path_to_repository_file+". Not found")

def add_to_file(files_to_add_to: list, path_to_repository: str) -> None:
    '''
    Takes a list of dictionaries configured as such in the config yml file:

    files-to-add-to:
    - file_paths: ['.buildkite/run_models.sh']
      insert_at_top: false
      new_line: run-operation fivetran_utils.drop_schemas --target "$db"
    
    Args:
    - files_to_add_to: list of dictionaries-version of the above
    - path_to_repository: path to the cloned repo (ie 'repositories/dbt_jira')
    '''
    for rule in files_to_add_to:
        insert_at_top = rule['insert_at_top']
        new_line = rule['new_line']

        for file in rule['file_paths']:
            try:
                print("Adding %s to file: %s..." %(new_line, file))
                path_to_repository_file = os.path.join(path_to_repository, file)
                repo_file = pathlib.Path(path_to_repository_file)
                if repo_file.exists():
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
                else:
                    print("Ignoring "+path_to_repository_file+". Not found")
            except Exception as e:
                print (u'\u2717', "Adding %s file %s. Error: %s..." %(new_line, file, e))

def uptick_project_version(current_version: str, bump_type: str) -> str:
    '''
    Takes a x.y.z project version and bump (major.minor.patch) and returns new project version.

    Args: 
    - current version of the project, parsed from its dbt_project.yml
    - bump type to be applied: "patch", "minor", "major"
    '''
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
    else: 
        print('Not a valid bump type. No change applied to project version.')
    new_version = ".".join(current_version_split)
    return new_version

def update_project(repo: github.Repository.Repository, path_to_repository: str, config: str) -> None:
    '''
    WIP: currently does not work consistently enough. Did not work in last rollout for 1/2 of packages

    Intention is to update all `dbt_project.yml` (root project and /integration_tests) for a major.minor.patch version bump

    Future ideas:
    - Creates changelog entry (can leveage add_to_file())
    '''
    files = ["dbt_project.yml","integration_tests/dbt_project.yml"]
    file_paths = []
    for f in files:
        file_paths.insert(0, os.path.join(path_to_repository, f))
        project_content = repo.get_contents(f)
        project = ruamel.yaml.load(
            project_content.decoded_content, # decoded_content is in bytes? perhaps stream should = contents
            Loader=ruamel.yaml.RoundTripLoader, # RoundTripLoader in ruamel.yaml is a loader that preserves the structure of the YAML document when loading it into a Python object. This means that the order of the keys in a dictionary, the order of the items in a list, and the nesting of objects will be preserved when the YAML document is loaded.
            preserve_quotes=True
        )

        try:
            old_version = project["version"]
            new_version = uptick_project_version(current_version = old_version, bump_type = config["version-bump-type"])

            path_to_repository_file = os.path.join(path_to_repository, f)

            # read in the file    
            with open(path_to_repository_file, 'r') as file:
                file_contents = file.read()

            # use re module to replace package version  
            new_contents = re.sub(old_version, new_version, file_contents)
            
            # use re to replace -- this currently isn't working
            # if f == "dbt_project.yml" and config["require-dbt-version"] is not None:
            #     print(type(project["require-dbt-version"]))
            #     print(type(config["require-dbt-version"]))
            #     old_dbt_version = project["require-dbt-version"]
            #     new_dbt_version = config["require-dbt-version"]
            #     new_contents = re.sub(old_dbt_version, new_dbt_version, file_contents)

            with open(path_to_repository_file, 'w') as file:
                file.write(new_contents)

        except github.GithubException as error:
            print("dbt project.yml files not found. Error: %s" %(error))

def update_packages(repo: github.Repository.Repository, branch_name: str, config: dict, source_bump_type: str) -> None:
    '''
    WIP: Currently, this function does not perform as easily as desired. Will need to be updated. 
    The intention is to update root packages.yml files such that a new version bump is incorporated for relevant packages without having to specify specific package versions for all packages.

    Future ideas:
    - add source package (or any package) bumping
    - update README dependency matrix as well 
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
                package["version"] = config['fivetran-utils-version'] # as set in the package_manager.yml
            if "package" in package and "fivetran" in package["package"] and source_bump_type != 'patch' and package["package"] != 'fivetran/fivetran_utils': # switch back to source
                old_vesion_range = package["version"]
                min_version = ''
                max_version = ''
                for char in old_vesion_range:
                    if char.isnumeric() or char == '.':
                        if min_version.count('.') < 2:
                            min_version = min_version + char
                        else:
                            max_version = max_version + char
                new_min_version = uptick_project_version(min_version, source_bump_type)
                new_max_version = uptick_project_version(max_version, source_bump_type)
                new_version_range = '[' + '">=' + new_min_version + '"' + ', "' + new_max_version + '"]'
                package['version'] = new_version_range

        repo.update_file(
            path=packages_content.path,
            message="Updating package dependencies",
            content=ruamel.yaml.dump(packages, Dumper=ruamel.yaml.RoundTripDumper),
            sha=packages_content.sha,
            branch=branch_name,
        )
    except github.GithubException:
        print("'packages.yml' not found in repo.")