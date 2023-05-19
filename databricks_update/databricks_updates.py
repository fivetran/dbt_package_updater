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

branch_name = 'MagicBot/databricks-compatibility'  # Name of the new branch to create

repo_file = load_yml('databricks_pkgs.yml')
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
        modified_content = modified_content + '\n' + '\n'.join(lines_to_add)
    if 'replace_text' in modification:
        old_text = modification['replace_text']['old_text']
        new_text = modification['replace_text']['new_text']
        modified_content = modified_content.replace(old_text, new_text)
    if 'add_to_front' in modification:
        lines_to_add = modification['add_to_front']
        modified_content = '\n'.join(lines_to_add)+ f'\n{modified_content}'
    if 'regex' in modification:
        pattern = modification['regex']['pattern']
        replacement = modification['regex']['replacement']
        modified_content = re.sub(pattern, replacement, modified_content)
    if 'chglog' in modification:
        pattern = modification['chglog']['pattern']
        replacement = modification['chglog']['replacement']
        modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)

    return modified_content

modifications = {
        '.buildkite/hooks/pre-command': {
            'add_lines': [
                'export CI_DATABRICKS_DBT_CATALOG=$(gcloud secrets versions access latest --secret="CI_DATABRICKS_DBT_CATALOG" --project="dbt-package-testing-363917")'
            ]
        },
        '.buildkite/pipeline.yml': {
            'add_lines': [
                '  - label: ":databricks: Run Tests - Databricks"',
                '    key: "run_dbt_databricks"',
                '    plugins:',
                '      - docker#v3.13.0:',
                '          image: "python:3.8"',
                '          shell: [ "/bin/bash", "-e", "-c" ]',
                '          environment:',
                '            - "BASH_ENV=/tmp/.bashrc"',
                '            - "CI_DATABRICKS_DBT_HOST"',
                '            - "CI_DATABRICKS_DBT_HTTP_PATH"',
                '            - "CI_DATABRICKS_DBT_TOKEN"',
                '            - "CI_DATABRICKS_DBT_CATALOG"',
                '    commands: |',
                '      bash .buildkite/scripts/run_models.sh databricks\n'
            ]
        },
        'integration_tests/ci/sample.profiles.yml': {
            'replace_text': {
                'old_text': 'catalog: null',
                'new_text': r'''catalog: "{{ env_var('CI_DATABRICKS_DBT_CATALOG') }}"'''
            }
        },
        'integration_tests/dbt_project.yml': {
            'add_lines': [
                'dispatch:',
                '  - macro_namespace: dbt_utils',
                '''    search_order: ['spark_utils', 'dbt_utils']'''
            ],
            'regex':{}
        },
        'integration_tests/requirements.txt': {
            'replace_text': {
                'old_text': r'dbt-redshift>=1.3.0,<2.0.0',
                'new_text': r'dbt-redshift>=1.3.0,<1.5.0'
            }
        },
        # dynamically set in for loop:
        'CHANGELOG.md': {},
        'models/src_': {}, 
        'dbt_project.yml': {}
    }

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

        modifications['CHANGELOG.md']['add_to_front'] = [
            f'# dbt_{short_name} v{next_version}',
            '## 🎉 Feature Update 🎉',
            f'- Databricks compatibility! ([#{next_pr}](https://github.com/fivetran/{repo_name}/pull/{next_pr}))\n'
        ]
        modifications['CHANGELOG.md']['chglog'] = {
            'pattern': f'# {repo_name} v0.UPDATE.UPDATE' + r'(.+?)' + re.escape('[templates](/.github).'),
            'replacement': f'''## 🚘 Under the Hood 🚘
- Incorporated the new `fivetran_utils.drop_schemas_automation` macro into the end of each Buildkite integration test job. {pkg_pr_link}
- Updated the pull request [templates](/.github). {pkg_pr_link}
'''
        }
        modifications['models/src_']['regex'] = {
            'pattern': r'database:.*".*"',
            'replacement': r"""database: "{% if target.type != 'spark' %}{{ var('""" + base_name + r'''_database', target.database)}}{% endif %}"'''
        }
        modifications['dbt_project.yml']['regex'] = {
            'pattern': r"version:.*'.*'",
            'replacement': f"version: {next_version}"
        }
        modifications['integration_tests/dbt_project.yml']['regex'] = {
            'pattern': r"version:.*'.*'",
            'replacement': f"version: {next_version}"
        }

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

        try:
            # Apply changes
            for file_path, modification in modifications.items():
                # Make the desired changes to the file
                try:
                    if 'models/src_' in file_path and '_source' in repo_name:
                        file_path = file_path + base_name +'.yml'
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

        # Commit the changes once it's all done
        os.system(f'git commit -am "{branch_name} updates"')

        # Push the changes to the remote repository
        os.system(f'git push origin HEAD:{branch_name}')

        print(f'Pushed updates to {repo_name} in the new branch {branch_name}')

        # Create PR now that the branch is pushed
        pr_title = 'Feature: Databricks compatibility'

        # Create PR
        if '_source' in repo_name:
            src_yml_update = f'- [ ] `{short_name}.yml` database logic updated\n' # only add this for source packages
        else:
            src_yml_update = ''
        pr_body = f'''Confirm the following files were correctly updated automatically:
- [ ] `hooks/pre-command` line added
- [ ] `pipeline.yml` section added
- [ ] `sample.profiles.yml` catalog updated
- [ ] `integration_tests/dbt_project.yml` section added (check for dupes though)
- [ ] Version updates for `dbt_project.yml` and `integration_tests/dbt_project.yml` (automatically moved to next breaking change)
- [ ] Changelog (automatically moved to next breaking change, but check the PR links were added correctly!)
{src_yml_update}
Manual updates are:
- [ ] `README` installation and dependencies
- [ ] `packages.yml` for transform packages
- [ ] Incremental Models
            '''
        pull_request = repo.create_pull(title=pr_title, body=pr_body, base='main', head=branch_name)
        pr_number = pull_request.number

        print(f"Pull request #{pr_number} created: {pull_request.html_url}")
        print(f'{repo_name} updates complete.')
        os.chdir('..')

    except Exception as e:
        print(f'Error updating {repo_name}: {str(e)}')

