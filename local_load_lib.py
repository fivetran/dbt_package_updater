# allows you to read, write, and parse YAML files
import yaml

# ruamel.yaml is a YAML 1.2 loader/dumper package for Python. It is a fork of the PyYAML library
# powerful and flexible YAML parser that can be used for a variety of tasks. It is a good choice for applications that require a high degree of control over the YAML format.
import ruamel.yaml

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