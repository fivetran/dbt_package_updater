# provides a number of classes and functions for representing and manipulating dates and times, as well as for formatting and parsing dates and times in a variety of formats.
from datetime import datetime

# allows you to interact with GitHub repositories and other GitHub resources. It is a wrapper around the GitHub REST API, which means that it allows you to perform all of the same actions that you can perform using the GitHub web interface.
import github

def set_defaults() -> str:
    '''
    set Branch name and commit messsage.
    Note that the branch_exists var is set in main() - make sure that if it's set to false, there is not branch with this name in the repo 
    
    Future: should this also set the default PR title? Should the default PR title = commit message?
    '''
    branch_name = 'MagicBot/' + "rollout-mass-updates-3" # update_pre_run
    commit_message = 'Mass package update rollout ' + str(datetime.today().year) + '-' + str(datetime.today().month)
    return branch_name, commit_message


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