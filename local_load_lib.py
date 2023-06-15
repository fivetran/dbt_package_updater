# allows you to read, write, and parse YAML files
import yaml

# ruamel.yaml is a YAML 1.2 loader/dumper package for Python. It is a fork of the PyYAML library
# powerful and flexible YAML parser that can be used for a variety of tasks. It is a good choice for applications that require a high degree of control over the YAML format.
import ruamel.yaml

# The os module in Python provides a portable way of using operating system dependent functionality. It provides a number of functions for interacting with the file system, processes, and other operating system resources.
import os

# high-level interface to the operating system's file manipulation functions. It provides a number of functions for copying, moving, deleting, and renaming files and directories.
import shutil

def load_configurations() -> dict:
    """
    Loads all configurations from `package_manager.yml` file located in root repo
    
    Returns:
    - dictionary object of configurations that were defined in yml
    """
    with open("package_manager.yml") as file:
        config = ruamel.yaml.load(file, Loader=ruamel.yaml.RoundTripLoader, preserve_quotes=True)        
    return config

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

def clear_working_directory(write_to_directory: str) -> None:
    '''
    Clears out the directory we want to write our changes to if it exists already.
    
    Args:
    - write_to_directory: where the cloned repos are stored (most likely 'repositories')
    '''
    ## Remove repositories folder with cloned repos if it exists
    if os.path.exists(write_to_directory +'/'):
        try: 
            shutil.rmtree(write_to_directory + '/')
        except OSError as e:
            raise OSError(f"The " + write_to_directory + " directory cannot be removed: {e}")