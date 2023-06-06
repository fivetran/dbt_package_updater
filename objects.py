# allows you to interact with GitHub repositories and other GitHub resources. It is a wrapper around the GitHub REST API, which means that it allows you to perform all of the same actions that you can perform using the GitHub web interface.
import github

## This file is not being used anywhere yet -- just a start

class Package:
    '''
    defining Package object
    '''
    name: str
    connectors: list
    version: str
    type: str
    repo: github.Repository.Repository
    default_branch = 'main'
    required_dbt_version: str

    def __init__(self, name, connectors, version, type, repo, default_branch, required_dbt_version):
        self.name = name
        self.connectors = connectors
        self.version = version
        self.type = type
        self.repo = repo
        self.default_branch = default_branch
        self.required_dbt_version = required_dbt_version


class Update:
    '''
    The mass-update we are applying.
    '''
    name: str
    repos: list
    added_files = []
    removed_files = []
    add_to_file_rules = {}
    find_and_replace_rules = {} 
    status: str