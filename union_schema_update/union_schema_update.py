import yaml
import re
import os
from github import Github
from math import floor

create_prs = 'true'
# create_prs = 'false'

# Function to load yaml files as dictionaries
def load_yml(yml_name) -> dict:
    with open(yml_name) as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents

# Function to add the source_relation condition to a match
def add_source_relation_join(match):
    existing_join = match.group(1)
    table_names = re.findall(r'[\w_]+', existing_join)  # Extract table names
    new_condition = f'and {table_names[3]}.source_relation = {table_names[5]}.source_relation'
    return existing_join + '\n        ' + new_condition

def add_line_after_date_day(match):
    try:
        original_line = match.group()  # Get the entire matched line
        table_name = re.search(r'([\w_]+)\.date_day', original_line).group(1)
        new_line_to_add = f'{table_name}.source_relation,'
    except:
        try:
            original_line = match.group()  # Get the entire matched line
            table_name = re.search(r'cast\(([\w_]+)\.\w+ as date\) as date_day,', original_line).group(1)
            new_line_to_add = f'{table_name}.source_relation,'
        except:
            original_line = match.group()  # Get the entire matched line
            table_name = ''
            new_line_to_add = f'{table_name}.source_relation,'
    return f'        {new_line_to_add}\n{original_line}'

def increment_groupby(match):
    original_number = int(match.group(1))
    new_number = str(original_number + 1)
    return f'{{{{ dbt_utils.group_by({new_number}) }}}}' 

def modify_file(file_content, modification):
    modified_content = file_content
    if 'add_lines' in modification:
        lines_to_add = modification['add_lines']
        modified_content = modified_content + f'\n{lines_to_add}'
    if 'replace_text' in modification:
        old_text = modification['replace_text']['old_text']
        new_text = modification['replace_text']['new_text']
        modified_content = modified_content.replace(old_text, new_text)
    if 'replace_text_2' in modification:
        old_text = modification['replace_text_2']['old_text']
        new_text = modification['replace_text_2']['new_text']
        modified_content = modified_content.replace(old_text, new_text)
    if 'replace_text_3' in modification:
        old_text = modification['replace_text_3']['old_text']
        new_text = modification['replace_text_3']['new_text']
        modified_content = modified_content.replace(old_text, new_text)
    if 'add_to_front' in modification:
        lines_to_add = modification['add_to_front']
        modified_content = lines_to_add + f'\n{modified_content}'
    if 'regex' in modification:
        pattern = modification['regex']['pattern']
        replacement = modification['regex']['replacement']
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.MULTILINE)
    if 'regex_2' in modification:
        pattern = modification['regex_2']['pattern']
        replacement = modification['regex_2']['replacement']
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.MULTILINE)
    if 'regex_3' in modification:
        pattern = modification['regex_3']['pattern']
        replacement = modification['regex_3']['replacement']
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.MULTILINE)
    if 'regex_4' in modification:
        pattern = modification['regex_4']['pattern']
        replacement = modification['regex_4']['replacement']
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.MULTILINE)
    return modified_content

branch_name = 'MagicBot/add-union-schema'  # Name of the new branch to create

repo_file = load_yml('union_schema_pkgs.yml')
repos = repo_file['repositories']

# Authenticate with Github API using personal access token
creds = load_yml('../credentials.yml')
access_token = creds['access_token']

# Create a PyGithub instance using the access token
g = Github(access_token)

try:
    os.mkdir('dbt_packages')
    os.chdir('dbt_packages')
except:
    os.chdir('dbt_packages')

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

        try:
            # Get next PR number
            pull_requests = repo.get_pulls(state='all')
            issues = repo.get_issues(state='all')
            all_items = list(pull_requests) + list(issues)
            max_number = max([item.number for item in all_items])
            next_pr = max_number + 1

            # Get package updater PR number
            # Search for the pull request by title
            pkg_pr_no = [pr.number for pr in pull_requests if pr.title == 'Package Updater PR'][0] 
        except:
            pkg_pr_no = 1
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

        # create docs if it doesn't exist.
        if not os.path.exists('models/docs.md'):
            with open('models/docs.md', 'w') as file:
                pass  # Creating a new blank file

        modifications = {'models/docs.md': {'add_lines': '''{% docs source_relation %}
The source of the record if the unioning functionality is being used. If not this field will be empty.
{% enddocs %}'''}}

        if 'source' in repo_name:
            modifications['CHANGELOG.md'] = {'add_to_front': f'''# dbt_{short_name} v{next_version}
[PR #{next_pr}](https://github.com/fivetran/{repo_name}/pull/{next_pr}) includes the following updates:
## Feature update 🎉
- Unioning capability! This adds the ability to union source data from multiple {base_name} connectors. Refer to the [README](https://github.com/fivetran/{repo_name}/blob/main/README.md) for more details.

## Under the hood 🚘
- Updated tmp models to union source data using the `fivetran_utils.union_data` macro. 
- To distinguish which source each field comes from, added `source_relation` column in each staging model and applied the `fivetran_utils.source_relation` macro.
- Updated tests to account for the new `source_relation` column.
'''}
            
        if 'source' not in repo_name:
            modifications['packages.yml'] = {'add_lines': f'''- git: https://github.com/fivetran/{repo_name}_source.git
  revision: MagicBot/add-union-schema
  warn-unpinned: false'''}

            modifications['CHANGELOG.md'] = {'add_to_front': f'''# dbt_{short_name} v{next_version}
[PR #{next_pr}](https://github.com/fivetran/{repo_name}/pull/{next_pr}) includes the following updates:
## Feature update 🎉
- Unioning capability! This adds the ability to union source data from multiple {base_name} connectors. Refer to the [README](https://github.com/fivetran/{repo_name}/blob/main/README.md) for more details.

## Under the hood 🚘
- In the source package, updated tmp models to union source data using the `fivetran_utils.union_data` macro. 
- To distinguish which source each field comes from, added `source_relation` column in each staging and downstream model and applied the `fivetran_utils.source_relation` macro.
- Updated tests to account for the new `source_relation` column.
    - The `source_relation` column is included in all joins and window function partition clauses in the transform package. 
'''}

        modifications['README.md'] = {'replace_text': {
            'old_text': r'<summary>Expand for configurations</summary>',
            'new_text': f'''<summary>Expand for configurations</summary>\n
### Union multiple connectors
If you have multiple {base_name} connectors in Fivetran and would like to use this package on all of them simultaneously, we have provided functionality to do so. The package will union all of the data together and pass the unioned table into the transformations. You will be able to see which source it came from in the `source_relation` column of each model. To use this functionality, you will need to set either the `{base_name}_union_schemas` OR `{base_name}_union_databases` variables (cannot do both) in your root `dbt_project.yml` file:

```yml
vars:
    {base_name}_union_schemas: ['{base_name}_usa','{base_name}_canada'] # use this if the data is in different schemas/datasets of the same database/project
    {base_name}_union_databases: ['{base_name}_usa','{base_name}_canada'] # use this if the data is in different databases/projects but uses the same schema name
```
Please be aware that the native `source.yml` connection set up in the package will not function when the union schema/database feature is utilized. Although the data will be correctly combined, you will not observe the sources linked to the package models in the Directed Acyclic Graph (DAG). This happens because the package includes only one defined `source.yml`.

To connect your multiple schema/database sources to the package models, follow the steps outlined in the [Union Data Defined Sources Configuration](https://github.com/fivetran/dbt_fivetran_utils/tree/releases/v0.4.latest#union_data-source) section of the Fivetran Utils documentation for the union_data macro. This will ensure a proper configuration and correct visualization of connections in the DAG.'''
}}

        modifications['dbt_project.yml'] = {'regex': {
            'pattern': r"^version:.*",
            'replacement': f"version: '{next_version}'"
        }}
        modifications['integration_tests/dbt_project.yml'] = {'regex': {
            'pattern': r"^version:.*",
            'replacement': f"version: '{next_version}'"
        }}

        # model_list = os.listdir('./models')

        model_list = []
        for root, dirs, files in os.walk('./models'):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                model_list.append(file_path.replace('./models/',''))

# # Modify the paths to only include the subfolder structure
# subfolder_file_paths = [os.path.relpath(path, model_directory) for path in all_file_paths]

        # Start rules for source vs transform
        if 'source' in repo_name:
            for model_name in model_list:
                if '.sql' in model_name and 'tmp' not in model_name:
                    modifications[f'models/{model_name}'] = {'replace_text': {
                    'old_text': 'from base',
                    'new_text': f'''\n        {{{{ fivetran_utils.source_relation(
            union_schema_variable='{base_name}_union_schemas', 
            union_database_variable='{base_name}_union_databases') 
        }}}}

    from base'''
}}
                    modifications[f'models/{model_name}']['regex'] = {
                    'pattern': r"final as \([\s\S]*?select",
                    'replacement': '''final as (\n
    select
        source_relation,'''}

            modifications[f'models/src_{base_name}.yml'] = {'replace_text': {
                'old_text': f'- name: {base_name}',
                'new_text': f'- name: {base_name} # This source will only be used if you are using a single {base_name} source connector. If multiple sources are being unioned, their tables will be directly referenced via adapter.get_relation.'
            }}

            modifications[f'models/stg_{base_name}.yml'] = {'add_to_front': 'UPDATE TESTS!!! (delete line when done.)'}
            modifications[f'models/stg_{base_name}.yml']['replace_text'] = {
                'old_text': '  columns:',
                'new_text': '''  columns:
      - name: source_relation
        description: "{{ doc('source_relation') }}"'''
            }

            modifications[f'models/stg_{base_name}.yml']['replace_text_2'] = {
                'old_text': '  combination_of_columns:',
                'new_text': '''  combination_of_columns:
            - source_relation'''
            }

            tmp_list = os.listdir('./models/tmp')
            for model_name in tmp_list:
                if '.sql' in model_name:
                    source_name = model_name.replace(f'stg_{base_name}__','').replace('_tmp.sql','')
                    modifications[f'models/tmp/{model_name}'] = {'regex': {
                        'pattern': r"(select\s*\*.*)(?:\r?\n.*)*",
                        'replacement': f'''{{{{
    fivetran_utils.union_data(
        table_identifier='{source_name}', 
        database_variable='{base_name}_database', 
        schema_variable='{base_name}_schema', 
        default_database=target.database,
        default_schema='{base_name}',
        default_variable='{source_name}',
        union_schema_variable='{base_name}_union_schemas',
        union_database_variable='{base_name}_union_databases'
    )
}}}}'''
}}

        if 'source' not in repo_name:
            if not os.path.exists(f'models/{base_name}.yml'):
                yml_name = base_name.replace('_ads','')
            else:
                yml_name = base_name
            modifications[f'models/{yml_name}.yml'] = {'add_to_front': 'UPDATE TESTS AND CHECK SOURCE_RELATION ADDED PROPERLY!!! (delete line when done.)'}
            modifications[f'models/{yml_name}.yml']['replace_text'] = {
                'old_text': '  columns:',
                'new_text': '''  columns:
      - name: source_relation
        description: "{{ doc('source_relation') }}"'''
            }
            modifications[f'models/{yml_name}.yml']['replace_text_2'] = {
                'old_text': '  combination_of_columns:',
                'new_text': '''  combination_of_columns:
            - source_relation'''
            }

        for model_name in model_list:
            if '.sql' in model_name:
                if 'source' not in repo_name:
                    modifications[f'models/{model_name}'] = {}
                    modifications[f'models/{model_name}']['regex_3'] = {
                        'pattern': r".*date_day,",
                        'replacement': add_line_after_date_day
                    }
                    modifications[f'models/{model_name}']['regex_4'] = {
                        'pattern': r"\{\{\s*dbt_utils\.group_by\((\d+)\)\s*\}}",
                        'replacement': increment_groupby
                    }
                modifications[f'models/{model_name}']['regex_2'] = {
                    'pattern': r"(join [\w_\s]+\n\s*on [\w_]+\.[\w_]+ = [\w_]+\.[\w_]+)",
                    'replacement': add_source_relation_join
                }

                modifications[f'models/{model_name}']['add_to_front'] = '''ADD source_relation WHERE NEEDED + CHECK JOINS AND WINDOW FUNCTIONS! (Delete this line when done.)\n'''

                modifications[f'models/{model_name}']['replace_text_2'] = {
                    'old_text': 'partition by',
                    'new_text': 'partition by source_relation,'
                }

        try:
            # Apply changes
            for file_path, modification in modifications.items():
                # Make the desired changes to the file
                try:
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

        if create_prs == 'true':
            # Commit the changes once it's all done
            os.system(f'git commit -am "{branch_name} updates"')

            # Push the changes to the remote repository
            os.system(f'git push origin HEAD:{branch_name}')

            print(f'Pushed updates to {repo_name} in the new branch {branch_name}')

            # Create PR now that the branch is pushed
            pr_title = 'Feature: Union schema compatibility'

            # Create PR
            pr_body = f'''Issue: 

Confirm the following files were correctly updated automatically:
- [ ] CHANGELOG
- [ ] README
- [ ] stg_{base_name}.yml, src_{base_name}.yml, {base_name}.yml (depending if source or transform)
- [ ] docs.md
- [ ] joins
- [ ] window functions (partition by)
- [ ] 'source_relation' column added in staging and transform models
- [ ] tests

Manual updates:
- [ ] Add `source_relation` to downstream models if necessary
- [ ] Finish any incomplete/incorrect joins/partitions
- [ ] Update tests to include `source_relation` in unique-combination-of-cols if necessary
    - May need to remove some uniqueness tests in favor of the combo test

Validation:
- [ ] `dbt run` locally passes
- [ ] `dbt test` locally passes
    '''
            pull_request = repo.create_pull(title=pr_title, body=pr_body, base='main', head=branch_name)
            pr_number = pull_request.number

            print(f"Pull request #{pr_number} created: {pull_request.html_url}")
            print(f'{repo_name} updates complete.')

        os.chdir('..')

    except Exception as e:
        print(f'Error updating {repo_name}: {str(e)}')

