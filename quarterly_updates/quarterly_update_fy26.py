import os
import re
import yaml
from github import Github
from math import floor
from datetime import datetime

# ----------------- CONFIG -----------------
# CREATE_PRS = False
CREATE_PRS = True
BRANCH_NAME = 'MagicBot/fy26-q2-updates'

FULL_GITIGNORE_BLOCK = """# dbt
**/package-lock.yml
package-lock.yml
.dbt/
dbt_modules/
dbt_packages/
logs/
profiles.yml
target/
*.log

# IDE files
.idea/
.vscode/
*~
*.swp
*.swo

# Jupyter Notebook
.ipynb_checkpoints

# OS generated files
**/.DS_Store
.DS_Store
.Spotlight-V100
.Trashes
._*
Thumbs.db
ehthumbs.db

# Python
*.egg
*.egg-info/
*.py[cod]
*.so
*$py.class
.Python
__pycache__/
build/
develop-eggs/
dist/
downloads/
eggs/
.env
.installed.cfg
lib/
lib64/
MANIFEST
parts/
sdist/
var/
wheels/

# Secrets and credentials
.env.*
.secrets
credentials.json
service-account.json

# Temporary files
.cache/
*.temp
*.tmp

# Virtual environments
.conda/
.env
.venv
ENV/
env/
env.bak/
venv/
venv.bak/
"""


def load_yml(yml_name) -> dict:
    with open(yml_name) as file:
        return yaml.load(file, Loader=yaml.FullLoader)

def write_if_missing(filepath, content):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            f.write(content)

# ok
def update_license_year(): 
    if os.path.exists('LICENSE'):
        with open('LICENSE', 'r+', encoding='utf-8') as f:
            lines = f.readlines()
            updated_lines = [
                '   Copyright © 2025 Fivetran Inc.\n' if 'Copyright [yyyy]' in line else line
                for line in lines
            ]
            f.seek(0)
            f.writelines(updated_lines)
            f.truncate()

# ok
def update_pipeline_py_version():
    if os.path.exists('.buildkite/pipeline.yml'):
        with open('.buildkite/pipeline.yml', 'r+') as f:
            content = f.read()
            updated = re.sub('python:3.8', 'python:3.10.13', content)
            f.seek(0)
            f.write(updated)
            f.truncate()

# ok
def update_requirements_certifi():
    if os.path.exists('integration_tests/requirements.txt'):
        with open('integration_tests/requirements.txt', 'a+') as f:
            f.seek(0)
            content = f.read()
            if 'certifi' not in content:
                f.write('\ncertifi==2025.1.31\n')

# ok
def update_gitignore():
    with open('.gitignore', 'w') as f:
        f.write(FULL_GITIGNORE_BLOCK)

# ok
def add_generate_docs_workflow():
    os.makedirs('.github/workflows', exist_ok=True)
    GENERATE_DOCS_TEMPLATE = f"""name: 'generate dbt docs'
on:
  pull_request:
    types:
      - labeled

jobs:
  generate-docs:
    if: github.event.label.name == 'docs:ready'
    uses: fivetran/dbt_package_automations/.github/workflows/generate-docs.yml@main
    secrets: inherit
    with:
      schema_var_name: {short_name}_schema"""

    write_if_missing('.github/workflows/generate-docs.yml', GENERATE_DOCS_TEMPLATE)

# ok
def patch_seeds_block_by_replacement(path='integration_tests/dbt_project.yml'):
    if not os.path.exists(path):
        print(f"{path} not found.")
        return

    with open(path, 'r') as f:
        lines = f.readlines()

    # Skip if +docs is already present
    if any('+docs' in line for line in lines):
        return False

    new_lines = []
    replaced = False

    for line in lines:
        if re.match(r'^\s*seeds:\s*$', line) and not replaced:
            indent = re.match(r'^(\s*)', line).group(1)
            new_lines.append(f'{indent}seeds:\n')
            new_lines.append(f'{indent}  +docs:\n')
            new_lines.append(f'{indent}    show: False\n')
            replaced = True
        else:
            new_lines.append(line)

    # If no seeds block at all, add it to the end
    if not replaced:
        new_lines.append('\nseeds:\n  +docs:\n    show: False\n')

    with open(path, 'w') as f:
        f.writelines(new_lines)

# ok
def standardize_md_headers():
    for root, _, files in os.walk('.'):
        for name in files:
            if name.lower() == 'readme.md':
                path = os.path.join(root, name)
                with open(path, 'r', encoding='utf-8') as f:
                    original_lines = f.readlines()

                tag_block = []
                content_lines = []
                in_tag_block = False
                h1_index = None

                # Step 1: Remove tag block and find H1
                for i, line in enumerate(original_lines):
                    if re.match(r'^\s*<p\b', line):
                        in_tag_block = True
                        tag_block = [line]
                        continue
                    if in_tag_block:
                        tag_block.append(line)
                        if re.search(r'</p>', line):
                            in_tag_block = False
                        continue
                    content_lines.append(line)

                if not tag_block:
                    continue  # no tag block to move

                h1_index = next((i for i, l in enumerate(content_lines) if re.match(r'^#\s+', l)), None)
                if h1_index is None:
                    continue  # no H1 to anchor under

                # Step 2: Check if already correct
                # Skip whitespace and check if the tag block already follows H1
                i = h1_index + 1
                while i < len(content_lines) and content_lines[i].strip() == '':
                    i += 1
                current_block = content_lines[i : i + len(tag_block)]
                if all(a.strip() == b.strip() for a, b in zip(current_block, tag_block)):
                    continue  # already in place

                # Step 3: Insert tag block after H1, with one blank line before and after
                rebuilt = []
                for i, line in enumerate(content_lines):
                    rebuilt.append(line)
                    if i == h1_index:
                        if not line.endswith('\n'):
                            rebuilt[-1] += '\n'
                        rebuilt.append('\n')
                        rebuilt.extend(tag_block)
                        if not tag_block[-1].endswith('\n'):
                            rebuilt[-1] += '\n'
                        rebuilt.append('\n')

                # Step 4: Remove any extra blank lines
                cleaned = []
                prev_blank = False
                for line in rebuilt:
                    if line.strip() == '':
                        if not prev_blank:
                            cleaned.append('\n')
                        prev_blank = True
                    else:
                        cleaned.append(line)
                        prev_blank = False

                if cleaned != original_lines:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.writelines(cleaned)

# ok
def update_auto_release_workflow():
    path = '.github/workflows/auto-release.yml'
    os.makedirs(os.path.dirname(path), exist_ok=True)

    new_script = """name: 'auto release'
on:
  pull_request:
    types:
      - closed
      - labeled

jobs:
  release:
    if: |
      (github.event.pull_request.merged == true && github.event.pull_request.base.ref == 'main') ||
      github.event.label.name == 'pre-release'
    uses: fivetran/dbt_package_automations/.github/workflows/auto-release.yml@feature/pre-release-support
    secrets: inherit
"""

    with open(path, 'w') as f:
        f.write(new_script)

def update_maintainer_pr_template():
    path = '.github/pull_request_template/maintainer_pull_request_template.md'
    os.makedirs(os.path.dirname(path), exist_ok=True)

    new_content = """<!--
Pre-Submission Reminders  
Before marking this PR as "ready for review":

- `dbt run --full-refresh && dbt test`  
- `dbt run` && `dbt test` (if incremental models are present)  
- The related issue is linked, tagged, and appropriately assigned  
- Documentation and version updates are included, if applicable  
- `docs` have been regenerated (unless there are no code or YAML changes)  
- BuildKite integration tests are passing
-->

## PR Overview 
**Package version introduced in this PR:** 
- 

**This PR addresses the following Issue/Feature(s):**
<!-- Add Issue # or internal ticket reference -->
- 

**Summary of changes:**  
<!-- 1-2 sentences describing PR changes. -->
- 

### Submission Checklist  
- [ ] Alignment meeting with the reviewer (if needed)  
  - [ ] Timeline and validation requirements discussed  
- [ ] Provide validation details:  
  - [ ] **Validation Steps:** Check for unintentional effects (e.g., add/run consistency & integrity tests)
  - [ ] **Testing Instructions:** Confirm the change addresses the issue(s)
  - [ ] **Focus Areas:** Complex logic or queries that need extra attention  
- [ ] Merge any relevant open PRs into this PR

### Changelog  
<!-- Recommend drafting changelog notes, then refining via ChatGPT using:  
"Draft a changelog entry based on the following notes." -->
- [ ] Draft changelog for PR  
- [ ] Final changelog for release review
"""

    with open(path, 'w') as f:
        f.write(new_content)

def update_readme_tags(path='README.md'):
    if not os.path.exists(path):
        print(f"{path} not found.")
        return

    if 'ga4' in repo_name or 'source' in repo_name:
        new_tags = f"""<p align="left">
    <a alt="License"
        href="https://github.com/fivetran/{repo_name}/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" /></a>
    <a alt="dbt-core">
        <img src="https://img.shields.io/badge/dbt_Core™_version->=1.3.0_,<2.0.0-orange.svg" /></a>
    <a alt="Maintained?">
        <img src="https://img.shields.io/badge/Maintained%3F-yes-green.svg" /></a>
    <a alt="PRs">
        <img src="https://img.shields.io/badge/Contributions-welcome-blueviolet" /></a>
</p>"""
    else:
        new_tags = f"""<p align="left">
    <a alt="License"
        href="https://github.com/fivetran/{repo_name}/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" /></a>
    <a alt="dbt-core">
        <img src="https://img.shields.io/badge/dbt_Core™_version->=1.3.0_,<2.0.0-orange.svg" /></a>
    <a alt="Maintained?">
        <img src="https://img.shields.io/badge/Maintained%3F-yes-green.svg" /></a>
    <a alt="PRs">
        <img src="https://img.shields.io/badge/Contributions-welcome-blueviolet" /></a>
    <a alt="Fivetran Quickstart Compatible"
        href="https://fivetran.com/docs/transformations/dbt/quickstart">
        <img src="https://img.shields.io/badge/Fivetran_Quickstart_Compatible%3F-yes-green.svg" /></a>
</p>"""

    with open(path, 'r+') as f:
        content = f.read()

        # Replace the entire first <p>...</p> block
        new_content, count = re.subn(r'<p[\s\S]*?</p>', new_tags.strip(), content, count=1)

        if count == 0:
            print(f"⚠️ No <p>...</p> tag block found in {path}. No changes made.")
            return

        f.seek(0)
        f.write(new_content)
        f.truncate()

def move_flags():
    profiles_path = 'integration_tests/ci/sample.profiles.yml'
    dbt_project_path = 'integration_tests/dbt_project.yml'

    # --- Remove flags from sample.profiles.yml ---
    with open(profiles_path, 'r') as f:
        lines = f.readlines()

    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('config:') or \
           stripped.startswith('send_anonymous_usage_stats') or \
           stripped.startswith('use_colors'):
            continue  # skip these lines
        cleaned_lines.append(line)

    updated_lines = []
    for line in cleaned_lines:
        # Replace threads: 2 → threads: 8
        line = re.sub('threads: 2', 'threads: 8', line)
        line = re.sub('threads: 4', 'threads: 8', line)
        line = re.sub('threads: 1', 'threads: 8', line)
        
        # Replace catalog: null → Jinja env var
        line = re.sub(
            r'catalog: null',
            "catalog: \"{{ env_var('CI_DATABRICKS_DBT_CATALOG') }}\"",
            line
        )

        updated_lines.append(line)

    # Collapse multiple blank lines into a single one
    collapsed_lines = []
    previous_blank = False

    for line in updated_lines:
        if line.strip() == '':
            if not previous_blank:
                collapsed_lines.append(line)
            previous_blank = True
        else:
            collapsed_lines.append(line)
            previous_blank = False

    with open(profiles_path, 'w') as f:
        f.writelines(collapsed_lines)

    # --- Append flags to dbt_project.yml if not present ---
    with open(dbt_project_path, 'r') as f:
        dbt_lines = f.read()

    if 'flags' not in dbt_lines:
        with open(dbt_project_path, 'a') as f:
            f.write('\nflags:')
    if 'send_anonymous_usage_stats' not in dbt_lines:
        with open(dbt_project_path, 'a') as f:
            f.write('\n  send_anonymous_usage_stats: False')
    if 'use_colors' not in dbt_lines:
        with open(dbt_project_path, 'a') as f:
            f.write('\n  use_colors: True')

def update_pipeline_for_databricks():
    path = '.buildkite/pipeline.yml'
    catalog_line = '            - "CI_DATABRICKS_DBT_CATALOG"\n'

    if not os.path.exists(path):
        print(f"⏭️  Skipping: {path} not found")
        return

    with open(path, 'r') as f:
        lines = f.readlines()

    already_has_catalog = any('CI_DATABRICKS_DBT_CATALOG' in line for line in lines)
    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        # Replace all :bricks: with :databricks:
        line = line.replace(':bricks:', ':databricks:')
        new_lines.append(line)

        # Insert after CI_DATABRICKS_DBT_TOKEN
        if not inserted and line.strip() == '- "CI_DATABRICKS_DBT_TOKEN"' and not already_has_catalog:
            new_lines.append(catalog_line)
            inserted = True

    with open(path, 'w') as f:
        f.writelines(new_lines)

def ensure_catalog_export_in_pre_command():
    path = '.buildkite/hooks/pre-command'
    export_line = ('export CI_DATABRICKS_DBT_CATALOG=$(gcloud secrets versions access latest --secret="CI_DATABRICKS_DBT_CATALOG" --project="dbt-package-testing-363917")\n')

    with open(path, 'r') as f:
        lines = f.readlines()

    if any('CI_DATABRICKS_DBT_CATALOG' in line for line in lines):
        return

    with open(path, 'a') as f:
        f.write('\n' + export_line)

def insert_mass_update_changelog(changelog_path='CHANGELOG.md'):
    # Get next PR number
    pull_requests = repo.get_pulls(state='all')
    issues = repo.get_issues(state='all')
    all_items = list(pull_requests) + list(issues)
    max_number = max([item.number for item in all_items])
    next_pr = max_number + 1
    changelog_entry = f"""[PR #{next_pr}](https://github.com/fivetran/{repo_name}/pull/{next_pr}) includes the following updates:

### Under the Hood - July 2025 Updates

- Updated conditions in `.github/workflows/auto-release.yml`.
- Added `.github/workflows/generate-docs.yml`.
- Added `+docs: show: False` to `integration_tests/dbt_project.yml`.
- Migrated `flags` (e.g., `send_anonymous_usage_stats`, `use_colors`) from `sample.profiles.yml` to `integration_tests/dbt_project.yml`.
- Updated `maintainer_pull_request_template.md` with improved checklist.
- Refreshed README tag block:
  - Standardized Quickstart-compatible badge set
  - Left-aligned and positioned below the H1 title.
- Updated Python image version to `3.10.13` in `pipeline.yml`.
- Added `CI_DATABRICKS_DBT_CATALOG` to:
  - `.buildkite/hooks/pre-command` (as an export)
  - `pipeline.yml` (under the `environment` block, after `CI_DATABRICKS_DBT_TOKEN`)
- Added `certifi==2025.1.31` to `requirements.txt` (if missing).
- Updated `.gitignore` to exclude additional DBT, Python, and system artifacts.
"""

    if not os.path.exists(changelog_path):
        print(f"⏭️  Skipping: {changelog_path} not found")
        return

    with open(changelog_path, 'r+') as f:
        existing = f.read()
        f.seek(0)
        f.write(changelog_entry + '\n' + existing)



#############################################################################################################################
# Load repos and credentials
repo_file = load_yml('packages.yml')
repos = repo_file['repositories']
creds = load_yml('../credentials.yml')
g = Github(creds['access_token'])
created_pr_links = []

os.makedirs('dbt_packages', exist_ok=True)
os.chdir('dbt_packages')

for repo_name in repos:
    short_name = repo_name.replace('dbt_', '').replace('_source', '')
    repo_url = f'https://github.com/fivetran/{repo_name}.git'
    repo_directory = repo_name
    repo = g.get_repo(f"fivetran/{repo_name}")

    # Clone or pull repo
    if not os.path.exists(repo_directory):
        os.system(f'git clone {repo_url} {repo_directory}')
    os.chdir(repo_directory)
    os.system('git pull')

    # Checkout or create branch
    os.system(f'git checkout -B {BRANCH_NAME}')

    # Apply updates
    update_license_year()
    update_pipeline_py_version()
    update_requirements_certifi()
    update_gitignore()
    add_generate_docs_workflow()
    patch_seeds_block_by_replacement()
    standardize_md_headers()
    update_auto_release_workflow()
    update_maintainer_pr_template()
    update_readme_tags()
    move_flags()
    update_pipeline_for_databricks()
    ensure_catalog_export_in_pre_command()
    insert_mass_update_changelog()

    # Commit changes
    os.system('git add .')
    os.system(f'git commit -m "Q2 FY26: Apply automated update."')

    if CREATE_PRS:
        os.system(f'git push --set-upstream origin {BRANCH_NAME}')
        pr = repo.create_pull(
            title='Q2 FY26 Automatic Package Updates',
            body='''## Review Checklist

- [ ] Docs Generator
  - [ ] `integration_tests/dbt_project.yml`: Add the `# @docs-include` / `# @docs-ignore` tags.
    - See [the docs](https://github.com/fivetran/dbt_package_automations?tab=readme-ov-file#generate-docs-source) and [Recharge's `dbt_project.yml`](https://github.com/fivetran/dbt_recharge/blob/main/integration_tests/dbt_project.yml) as guides for how to use the tags. 
  - [ ] `generate-docs.yml`: confirm the correct `schema_var_name` is set.
    - See [Recharge's `generate-docs.yml`](https://github.com/fivetran/dbt_recharge/blob/main/.github/workflows/generate-docs.yml) for an example.
- [ ] Check for any indentation issues in YAML file changes (especially `+docs: show: False` in `integration_tests/dbt_project.yml` .
- [ ] Update the `CHANGELOG`.

## Summary of Changes

### CI & Automation
- Updated conditions in `.github/workflows/auto-release.yml`.
- Added `.github/workflows/generate-docs.yml`.

### Testing Configuration
- **`integration_tests/dbt_project.yml`:**
  - Added `+docs: show: False`.
  - Migrated `flags` from `sample.profiles.yml` (e.g., `send_anonymous_usage_stats`, `use_colors`).

### Package Metadata & Docs
- Updated `maintainer_pull_request_template.md`.
- Refreshed all README tags:
  - Standardized to include Quickstart compatibility.
  - Ensured they are left-aligned and located under the H1 title.

### Runtime & Environment
- Updated `pipeline.yml`:
  - Changed Python image to `3.10.13`.
  - Inserted `CI_DATABRICKS_DBT_CATALOG` in `environment` block (if missing).
- Added export of `CI_DATABRICKS_DBT_CATALOG` in `.buildkite/hooks/pre-command` (if missing).
- Updated `.gitignore`.

### Python Dependencies
- Added `certifi==2025.1.31` to `requirements.txt` (if missing).
''',
            head=BRANCH_NAME,
            base='main'
        )

        pr.add_to_labels("next-release")
        created_pr_links.append(f"https://github.com/fivetran/{repo_name}/pull/{pr.number}")
    print(f"✅ {repo_name} complete.")
    os.chdir('..')  # Return to dbt_packages

print("Mass update complete.")
if created_pr_links:
    print("\n📦 Created PRs:")
    for link in created_pr_links:
        print(f"- {link}")