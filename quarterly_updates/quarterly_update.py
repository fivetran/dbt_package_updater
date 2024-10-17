import yaml
import re
import os
from github import Github
from math import floor

# create_prs = 'true'
create_prs = 'false'

# Function to load yaml files as dictionaries
def load_yml(yml_name) -> dict:
    with open(yml_name) as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents

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

branch_name = 'MagicBot/2024-q3-updates'  # Name of the new branch to create

repo_file = load_yml('quarterly_update_pkgs.yml')
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
        current_release = repo.get_latest_release().tag_name #.strip('v')
        latest_release = floor(float(current_release.strip('v0.')) + 1)
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

        new_macro_file = 'macros/is_incremental_compatible.sql'
        # create macro file
        if not os.path.exists(new_macro_file):
            with open(new_macro_file, 'w') as file:
                file.write('''{% macro is_incremental_compatible() %}
    {% if target.type in ('databricks') %}
        {% set re = modules.re %}
        {% set path_match = target.http_path %}
        {% set regex_pattern = "sql/protocol" %}
        {% set match_result = re.search(regex_pattern, path_match) %}
        {% if match_result %}
            {{ return(True) }}
        {% else %}
            {{ return(False) }}
        {% endif %}
    {% elif target.type in ('bigquery','snowflake','postgres','redshift') %}
        {{ return(True) }}
    {% else %}
        {{ return(False) }}
    {% endif %}
{% endmacro %}
''')
            os.system(f'git add {new_macro_file}')

# Define modifications below
        modifications = {}

        modifications['.buildkite/hooks/pre-command'] = {'add_lines': '''export CI_DATABRICKS_SQL_DBT_HTTP_PATH=$(gcloud secrets versions access latest --secret="CI_DATABRICKS_SQL_DBT_HTTP_PATH" --project="dbt-package-testing-363917")
export CI_DATABRICKS_SQL_DBT_TOKEN=$(gcloud secrets versions access latest --secret="CI_DATABRICKS_SQL_DBT_TOKEN" --project="dbt-package-testing-363917")'''}

        modifications['.buildkite/pipeline.yml'] = {'add_lines': '''
  - label: ":databricks: :database: Run Tests - Databricks SQL Warehouse"
    key: "run_dbt_databricks_sql"
    plugins:
      - docker#v3.13.0:
          image: "python:3.8"
          shell: [ "/bin/bash", "-e", "-c" ]
          environment:
            - "BASH_ENV=/tmp/.bashrc"
            - "CI_DATABRICKS_DBT_HOST"
            - "CI_DATABRICKS_SQL_DBT_HTTP_PATH"
            - "CI_DATABRICKS_SQL_DBT_TOKEN"
            - "CI_DATABRICKS_DBT_CATALOG"
    commands: |
      bash .buildkite/scripts/run_models.sh databricks-sql'''}

        modifications['.buildkite/scripts/run_models.sh'] = {'replace_text_2': {
            'old_text': '''dbt run-operation fivetran_utils.drop_schemas_automation --target "$db"''',
            'new_text': '''fi
dbt run-operation fivetran_utils.drop_schemas_automation --target "$db"'''
        }}

        modifications['.buildkite/scripts/run_models.sh']['replace_text'] = {
            'old_text': 'dbt deps',
            'new_text': f'''dbt deps
if [ "$db" = "databricks-sql" ]; then
dbt seed --vars '{{{short_name}_schema: {short_name}_sqlw_tests}}' --target "$db" --full-refresh
dbt compile --vars '{{{short_name}_schema: {short_name}_sqlw_tests}}' --target "$db"
dbt run --vars '{{{short_name}_schema: {short_name}_sqlw_tests}}' --target "$db" --full-refresh
dbt test --vars '{{{short_name}_schema: {short_name}_sqlw_tests}}' --target "$db"
dbt run --vars '{{{short_name}_schema: {short_name}_sqlw_tests}}' --target "$db"
dbt test --vars '{{{short_name}_schema: {short_name}_sqlw_tests}}' --target "$db"
else'''}

        modifications['CHANGELOG.md']= {'add_to_front': f'''# dbt_{short_name} v{next_version}

[PR #{next_pr}](https://github.com/fivetran/{repo_name}/pull/{next_pr}) includes the following updates:

## 🚨 Breaking Changes 🚨
> ⚠️ Since the following changes result in the table format changing, we recommend running a `--full-refresh` after upgrading to this version to avoid possible incremental failures.

- For Databricks All-Purpose clusters, incremental models will now be materialized using the delta table format (previously parquet).
  - Delta tables are generally more performant than parquet and are also more widely available for Databricks users. This will also prevent compilation issues on customers' managed tables.

- For Databricks SQL Warehouses, incremental materialization will not be used due to the incompatibility of the `insert_overwrite`  strategy.

## Under the Hood
- The `is_incremental_compatible` macro has been added to return `true` if the target warehouse supports our chosen incremental strategy.
  - This update was applied as there have been other Databricks runtimes discovered (ie. an endpoint and external runtime) which do not support the `insert_overwrite` incremental strategy used. '''}

        modifications['dbt_project.yml'] = {'regex': {
            'pattern': r"^version:.*",
            'replacement': f"version: '{next_version}'"
        }}

        modifications['integration_tests/dbt_project.yml'] = {'regex': {
            'pattern': r"^version:.*",
            'replacement': f"version: '{next_version}'"
        }}

        modifications['integration_tests/dbt_project.yml']['add_lines'] = f'''# Check if the models section already exists!!!
models:
  +schema: "{{{{ '{short_name}_sqlw_tests' if target.name == 'databricks-sql' else '{short_name}' }}}}"'''

        modifications['integration_tests/ci/sample.profiles.yml'] = {'replace_text': {
            'old_text': "threads: 2",
            'new_text': "threads: 8"
        }}
        modifications['integration_tests/ci/sample.profiles.yml']['replace_text_2'] = {
            'old_text': '''catalog: null''',
            'new_text': r'''catalog: "{{ env_var('CI_DATABRICKS_DBT_CATALOG') }}"'''
        }
        modifications['integration_tests/ci/sample.profiles.yml']['add_lines'] = f'''    databricks-sql:
      catalog: "{{{{ env_var('CI_DATABRICKS_DBT_CATALOG') }}}}"
      host: "{{{{ env_var('CI_DATABRICKS_DBT_HOST') }}}}"
      http_path: "{{{{ env_var('CI_DATABRICKS_SQL_DBT_HTTP_PATH') }}}}"
      schema: {short_name}_sqlw_tests
      threads: 8
      token: "{{{{ env_var('CI_DATABRICKS_SQL_DBT_TOKEN') }}}}"
      type: databricks'''


        model_list = []
        for root, dirs, files in os.walk('./models'):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                model_list.append(file_path.replace('./models/',''))

# # Modify the paths to only include the subfolder structure
# subfolder_file_paths = [os.path.relpath(path, model_directory) for path in all_file_paths]

        # Start rules for source vs transform
        for model_name in model_list:
            modifications[f'models/{model_name}'] = {'regex': {
            'pattern': r"materialized\s*=\s*'incremental',",
            'replacement': "materialized='incremental' if is_incremental_compatible() else 'table',"
            }}

            modifications[f'models/{model_name}']['replace_text'] = {
            'old_text': 'parquet',
            'new_text': 'delta'
            }

# Write the Modifications
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

        # Special README section ###################
            # Increase header level
            with open('README.md', 'r') as file:
                content = file.readlines()

            # Define the regex pattern for headers
            header_pattern = re.compile(r'^(#{1,6})\s(.*)$')

            # Initialize a flag to skip the first header
            first_header = True

            # List to store the updated lines
            updated_content = []

            for line in content:
                match = header_pattern.match(line)
                if match:
                    if first_header:
                        first_header = False
                        updated_content.append(line)  # Keep the first header as is
                    else:
                        header_level = match.group(1)
                        header_text = match.group(2)
                        new_header_level = '#' * (len(header_level) + 1)
                        updated_content.append(f'{new_header_level} {header_text}\n')
                else:
                    updated_content.append(line)

            # Write the updated content back to the file
            with open('README.md', 'w') as file:
                file.writelines(updated_content)
        ############################################

        except Exception as e:
            print(f'Error applying changes to {file_path}. {e}')

        if create_prs == 'true':
            # Commit the changes once it's all done
            os.system(f'git commit -am "{branch_name} updates"')

            # Push the changes to the remote repository
            os.system(f'git push origin HEAD:{branch_name}')

            print(f'Pushed updates to {repo_name} in the new branch {branch_name}')

            # Create PR now that the branch is pushed
            pr_title = '2024 Q3 Updates'

            # Create PR
            pr_body = f'''Issue: 

Confirm the following files were correctly updated automatically:
- [ ] .buildkite/pipeline.yml
- [ ] .buildkite/scripts/run_models.sh
- [ ] CHANGELOG
- [ ] README header level bumps
- [ ] dbt_project.yml version bumps
- [ ] integration_tests/dbt_project.yml models +schema
  - Check if this created a duplicate models section
- [ ] macros/is_incremental_compatible.sql

Manual updates:
- [ ] Bump versions in README

Validation:
- [ ] `dbt run` locally passes
- [ ] `dbt test` locally passes
- [ ] buildkite Databricks sql warehouse
    '''
            pull_request = repo.create_pull(title=pr_title, body=pr_body, base='main', head=branch_name)
            pr_number = pull_request.number

            print(f"Pull request #{pr_number} created: {pull_request.html_url}")
            print(f'{repo_name} updates complete.')

        os.chdir('..')

    except Exception as e:
        print(f'Error updating {repo_name}: {str(e)}')

