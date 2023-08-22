import yaml
import re
import os
from github import Github
from math import floor

# Function to load yaml files as dictionaries
def load_yml(yml_name) -> dict:
    with open(yml_name) as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents

# Function to add the source_relation condition to a match
def add_source_relation(match):
    existing_join = match.group(1)
    table_names = re.findall(r'[\w_]+', existing_join)  # Extract table names
    new_condition = f'and {table_names[4]}.source_relation = {table_names[6]}.source_relation'
    return existing_join + '\n        ' + new_condition

branch_name = 'MagicBot/add-union-schema'  # Name of the new branch to create

repo_file = load_yml('union_schema_pkgs.yml')
repos = repo_file['repositories']

# Authenticate with Github API using personal access token
creds = load_yml('../credentials.yml')
access_token = creds['access_token']

# Create a PyGithub instance using the access token
g = Github(access_token)

def modify_file(file_content, modification):
    modified_content = file_content
    if 'add_lines' in modification:
        lines_to_add = modification['add_lines']
        modified_content = modified_content + f'\n{lines_to_add}'
    if 'replace_text' in modification:
        old_text = modification['replace_text']['old_text']
        new_text = modification['replace_text']['new_text']
        modified_content = modified_content.replace(old_text, new_text)
    if 'add_to_front' in modification:
        lines_to_add = modification['add_to_front']
        modified_content = lines_to_add + f'\n{modified_content}'
    if 'regex' in modification:
        pattern = modification['regex']['pattern']
        replacement = modification['regex']['replacement']
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.MULTILINE)

    return modified_content

try:
    os.mkdir('dbt_packages')
    os.chdir('dbt_packages')
except:
    os.chdir('dbt_packages')

modifications = {'models/docs.md': {'add_lines': '''\n{% docs source_relation %}
The source of the record if the unioning functionality is being used. If not this field will be empty.
{% enddocs %}'''}}

for repo_name in repos:
    try:
        short_name = repo_name.replace('dbt_', '')
        base_name = short_name.replace('_source', '')
        # Clone the repository locally
        repo_directory = repo_name
        repo_url = f'https://github.com/fivetran/{repo_name}.git'

        # Get the remote repository info
        repo = g.get_repo(f"fivetran/{repo_name}")

        # Determine next version
        latest_release = floor(float(repo.get_latest_release().tag_name.strip('v0.')) + 1)
        next_version = '0.' + str(latest_release) + '.0'

        # Get next PR number
        pull_requests = repo.get_pulls(state='all')
        issues = repo.get_issues(state='all')
        all_items = list(pull_requests) + list(issues)
        max_number = max([item.number for item in all_items])
        next_pr = max_number + 1

        # Get package updater PR number
        # Search for the pull request by title
        pkg_pr_no = [pr.number for pr in pull_requests if pr.title == 'Package Updater PR'][0] 
        pkg_pr_link = f'([#{pkg_pr_no}](https://github.com/fivetran/{repo_name}/pull/{pkg_pr_no}))'

        try:
            # Navigate into the cloned repository directory
            os.chdir(repo_directory)
            os.system(f'git pull')
            print(f'Pulled {repo_name}.')
        except:
            os.system(f'git clone {repo_url} {repo_directory}')
            # Navigate into the cloned repository directory
            os.chdir(repo_directory)
            print(f'Cloned {repo_name}.')

        try:
            os.system(f'git checkout -b {branch_name}')
            print(f'Branch {branch_name} created in repository {repo_name}')
        except:
            os.system(f'git switch {branch_name}')
            print(f'Switched to {branch_name} in repository {repo_name}')

        modifications['CHANGELOG.md'] = {'add_to_front': f'''# dbt_{short_name} v{next_version}
[PR #{next_pr}](https://github.com/fivetran/{repo_name}/pull/{next_pr}) includes the following updates:
## Feature update 🎉
- Unioning capability! This adds the ability to union source data from multiple {base_name} connectors. Refer to the [README](https://github.com/fivetran/{repo_name}/blob/main/README.md) for more details.

## Under the hood 🚘
- Updated tmp models to union source data using the `fivetran_utils.union_data` macro. 
- To distinguish which source each field comes from, added `source_relation` column in each staging model and applied the `fivetran_utils.source_relation` macro.
- Updated tests to account for the new `source_relation` column.
'''}

        modifications['README.md'] = {'replace_text': {
            'old_text': r'<summary>Expand for configurations</summary>',
            'new_text': f'''<summary>Expand for configurations</summary>\n
### Unioning Multiple Connectors
If you have multiple {base_name} connectors in Fivetran and would like to use this package on all of them simultaneously, we have provided functionality to union the data together and pass the unioned table into the transformations. You will be able to see which source it came from in the `source_relation` column of each model. To use this functionality, you will need to set either the `{base_name}_union_schemas` or `{base_name}_union_databases` variables like the following example (**note that you cannot use both**):

```yml
vars:
  {base_name}_source:
    {base_name}_union_schemas: ['{base_name}_usa','{base_name}_canada'] # use this if the data is in different schemas/datasets of the same database/project
    {base_name}_union_databases: ['{base_name}_usa','{base_name}_canada'] # use this if the data is in different databases/projects but uses the same schema name
```'''}}

        modifications[f'models/src_{base_name}.yml'] = {'replace_text': {
            'old_text': f'- name: {base_name}',
            'new_text': f'- name: {base_name} # This source will only be used if you are using a single {base_name} source connector. If multiple sources are being unioned, their tables will be directly referenced via adapter.get_relation.'
        }}

        modifications['dbt_project.yml'] = {'regex': {
            'pattern': r"^version:.*",
            'replacement': f"version: '{next_version}'"
        }}
        modifications['integration_tests/dbt_project.yml'] = {'regex': {
            'pattern': r"^version:.*",
            'replacement': f"version: '{next_version}'"
        }}

        model_list = os.listdir('./models')
        # for model_name in model_list:
        #     modifications[f'models/{model_name}'] = {'regex_2': {
        #             'pattern': r"(left join [\w_]+\n\s*on [\w_]+\.[\w_]+ = [\w_]+\.[\w_]+)",
        #             'replacement': add_source_relation
        #     }}
        #     modifications['CHANGELOG.md'] = {'add_to_front': '''ADD source_relation WHERE NEEDED + CHECK JOINS AND WINDOW FUNCTIONS! (Delete this line when done.)\n'''}

        #     modifications[f'models/{model_name}'] = {'replace_text_2': {
        #         'old_text': 'partition by',
        #         'new_text': 'partition by source_relation, '
        #     }}

        # Start rules for source vs transform
        # get tmp files
        if '_source' in repo_name:
            # modifications[f'stg_{base_name}.yml'] = {'add_to_front': 'UPDATE TESTS!!! (delete line when done.)'}
            modifications[f'stg_{base_name}.yml'] = {'replace_text': {
                'old_text': 'columns:',
                'new_text': '''columns:
      - name: source_relation
        description: "{{ doc('source_relation') }}"\n'''
            }}
            
            for model_name in model_list:
                if '.sql' in model_name and 'tmp' not in model_name:
                    modifications[f'models/{model_name}'] = {'replace_text': {
                        'old_text': '    from base',
                        'new_text': f'''\n        {{{{ fivetran_utils.source_relation(
                union_schema_variable='{base_name}_union_schemas', 
                union_database_variable='{base_name}_union_databases') 
            }}}}

    from base'''
                }}
                    modifications[f'models/{model_name}'] = {'regex': {
                        'pattern': r"final as \([\s\S]*?select",
                        'replacement': '''final as (\n
    select
        source_relation,'''
                    }}
                    print(modifications[f'models/{model_name}'])

                if '.sql' in model_name and 'tmp' in model_name:
                    source_name = model_name.replace(f'stg_{base_name}__','').replace('_tmp.sql','')
                    modifications[f'models/tmp/{model_name}'] = {'regex': {
                        'pattern': r"(\n|.)*\n",
                        'replacement': f'''{{{{
        fivetran_utils.union_data(
            table_identifier='{source_name}', 
            database_variable='{base_name}_database', 
            schema_variable='{base_name}_schema', 
            default_database=target.database,
            default_schema='{base_name}',
            default_variable='{source_name}_source',
            union_schema_variable='{base_name}_union_schemas',
            union_database_variable='{base_name}_union_databases'
        )
    }}}}'''
                    }}

    #     if '_source' not in repo_name:
    #         # modifications[f'{base_name}.yml'] = {'add_to_front': 'UPDATE TESTS!!! (delete line when done.)'}
    #         modifications[f'{base_name}.yml'] = {'replace_text': {
    #             'old_text': 'columns:',
    #             'new_text': '''columns:
    #   - name: source_relation
    #     description: "{{ doc('source_relation') }}"\n'''
    #         }}

        try:
            # Apply changes
            for file_path, modification in modifications.items():
                # Make the desired changes to the file
                try:
                    # if 'models/src_' in file_path and '_source' in repo_name:
                    #     file_path = file_path + base_name +'.yml'
                    with open(file_path, 'r') as file:
                        existing_content = file.read()
                except:
                    continue
                # Modify the file content
                modified_content = modify_file(existing_content, modification)

                # Write changes to the file
                with open(file_path, 'w') as file:
                    file.write(modified_content)
                print(f'Applied changes to {repo_name}: {file_path}.')

        except Exception as e:
            print(f'Error applying changes to {file_path}. {e}')

#         # Commit the changes once it's all done
#         os.system(f'git commit -am "{branch_name} updates"')

#         # Push the changes to the remote repository
#         os.system(f'git push origin HEAD:{branch_name}')

#         print(f'Pushed updates to {repo_name} in the new branch {branch_name}')

#         # Create PR now that the branch is pushed
#         pr_title = 'Feature: Databricks compatibility'

#         # Create PR
#         if '_source' in repo_name:
#             src_yml_update = f'- [ ] `{short_name}.yml` database logic updated\n' # only add this for source packages
#         else:
#             src_yml_update = ''
#         pr_body = f'''Confirm the following files were correctly updated automatically:
# - [ ] `hooks/pre-command` line added
# - [ ] `pipeline.yml` section added
# - [ ] `sample.profiles.yml` catalog updated
# - [ ] `integration_tests/dbt_project.yml` section added (check for dupes though)
# - [ ] Version updates for `dbt_project.yml` and `integration_tests/dbt_project.yml` (automatically moved to next breaking change)
# - [ ] Changelog (automatically moved to next breaking change, but check the PR links were added correctly!)
# {src_yml_update}
# Manual updates are:
# - [ ] `README` installation and dependencies
# - [ ] `packages.yml` for transform packages
# - [ ] Incremental Models
#             '''
#         pull_request = repo.create_pull(title=pr_title, body=pr_body, base='main', head=branch_name)
#         pr_number = pull_request.number

#         print(f"Pull request #{pr_number} created: {pull_request.html_url}")
#         print(f'{repo_name} updates complete.')
        os.chdir('..')

    except Exception as e:
        print(f'Error updating {repo_name}: {str(e)}')

