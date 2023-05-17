import yaml
import re
import os

# Function to load yaml files as dictionaries
def load_yml(yml_name) -> dict:
    with open(yml_name) as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents

base_url = 'https://api.github.com'
branch_name = 'MagicBot/databricks-compatibility'  # Name of the new branch to create

repo_file = load_yml('../packages.yml')
repos = repo_file['repositories']

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
            '      bash .buildkite/scripts/run_models.sh databricks'
        ]
    },
    'integration_tests/ci/sample.profiles.yml': {
        'replace_text': {
            'old_text': 'catalog: null',
            'new_text': '''catalog: "{{ env_var('CI_DATABRICKS_DBT_CATALOG') }}"'''
        }
    },
    'integration_tests/dbt_project.yml': {
        'add_lines': [
            'dispatch:',
            '  - macro_namespace: dbt_utils',
            '''    search_order: ['spark_utils', 'dbt_utils']'''
        ]
    },
    'CHANGELOG.md': {
        'changelog': [
            '## 🎉 Feature Update 🎉',
            '- Databricks compatibility! ([#__](https://github.com/fivetran/dbt_mixpanel/pull/##))\n'
        ]
    },
    'models/src_': {
        'src_yml'
    }
}

def modify_file(file_content, modification, short_name):
    if 'add_lines' in modification:
        lines_to_add = modification['add_lines']
        modified_content = file_content + '\n' + '\n'.join(lines_to_add)
    elif 'replace_text' in modification:
        old_text = modification['replace_text']['old_text']
        new_text = modification['replace_text']['new_text']
        modified_content = file_content.replace(old_text, new_text)
    elif 'changelog' in modification:
        lines_to_add = modification['changelog']
        new_header = f'# dbt_{short_name} v0.X.X\n'
        modified_content = new_header + '\n'.join(lines_to_add)+ '\n' + file_content + '\n'
    elif 'src_yml' in modification:
        pattern = r'database:.*".*"'
        replacement = r"""database: "{% if target.type != 'spark' %}{{ var('""" + short_name + r'''_database', target.database)}}{% endif %}"'''
        modified_content = re.sub(pattern, replacement, file_content)
    else:
        modified_content = file_content
    
    return modified_content

try:
    os.mkdir('dbt_packages')
    os.chdir('dbt_packages')
except:
    os.chdir('dbt_packages')

for repo_name in repos:

    short_name = repo_name.replace('dbt_','').replace('_source','')
    print(f'Starting updates for {short_name}')

    try:
        # Clone the repository locally
        repo_directory = repo_name
        repo_url = f'https://github.com/fivetran/{repo_name}.git'
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
                    if 'src_yml' in modification:
                        file_path = file_path + short_name +'.yml'
                    with open(file_path, 'r') as file:
                        existing_content = file.read()
                except:
                    print(f'Could not open {repo_name}:{file_path}, or it does not exist.')
                    continue

                # Modify the file content
                modified_content = modify_file(existing_content, modification, short_name)

                # Write changes to the file
                with open(file_path, 'w') as file:
                    file.write(modified_content)
                print(f'Applied changes to {repo_name}: {file_path}.')

        except Exception as e:
            print(f'Error applying changes to {file_path}. {e}')

        # # Commit the changes once it's all done
        # os.system(f'git commit -am "{branch_name} updates"')

        # # Push the changes to the remote repository
        # os.system(f'git push origin HEAD:{branch_name}')

        # print(f'Successfully pushed updates to {repo_name} in the new branch {branch_name}')

    except Exception as e:
        print(f'Error updating {repo_name}: {str(e)}')

    os.chdir('..')
