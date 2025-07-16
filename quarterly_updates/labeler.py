from github import Github
import os
from pathlib import Path
import yaml

# --- CONFIG ---
LABEL_NAME = "docs:ready"
LABEL_COLOR = "1ad66f"  # Use hex without the "#"
LABEL_DESCRIPTION = "Triggers the docs generator workflow."  # Optional

# --- FUNCTIONS ---
def load_yml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def ensure_label_exists(repo, name, color, description=None):
    try:
        label = repo.get_label(name)
        label.edit(name=name, color=color, description=description or "")
        print(f"✏️ Updated label '{name}' in {repo.name} with new color/description")
    except:
        label = repo.create_label(name=name, color=color, description=description or "")
        print(f"➕ Created label '{name}' in {repo.name}")
    return label

# --- LOAD CREDS & REPOS ---
repo_file = load_yml('packages.yml')
repos = repo_file['repositories']
creds = load_yml('../credentials.yml')
g = Github(creds['access_token'])

os.makedirs('dbt_packages', exist_ok=True)
os.chdir('dbt_packages')

# --- ADD LABEL TO EACH REPO ---
for repo_name in repos:
    short_name = repo_name.replace('dbt_', '').replace('_source', '')
    repo_url = f'https://github.com/fivetran/{repo_name}.git'
    repo_directory = repo_name

    print(f"\nProcessing repository: {repo_name}")
    repo = g.get_repo(f"fivetran/{repo_name}")
    ensure_label_exists(repo, LABEL_NAME, LABEL_COLOR, LABEL_DESCRIPTION)