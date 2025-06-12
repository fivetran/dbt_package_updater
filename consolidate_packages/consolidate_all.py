# Update your credentials.yml, then run this file.

import os
import subprocess
import shutil
import yaml
import argparse
import re
from consolidate_dbt_packages import consolidate_dbt_package

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.join(SCRIPT_DIR, "tmp")
YAML_LIST_PATH = os.path.join(SCRIPT_DIR, "package_list.yml")
CRED_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "dbt_package_updater/credentials.yml"))
BRANCH_NAME = "MagicBot/consolidate-source"
REPO_OWNER = "fivetran"

# --- Loaders ---
def load_package_list(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f).get("repositories", [])

def load_credentials(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# --- Git ---
def clone_repo(repo_name, dest_path, username, token):
    url = f"https://{username}:{token}@github.com/{REPO_OWNER}/{repo_name}.git"
    subprocess.run(["git", "clone", url, dest_path], check=True)

def run_git_branch_setup(transform_path):
    subprocess.run(["git", "checkout", "main"], cwd=transform_path, check=True)
    subprocess.run(["git", "pull", "origin", "main"], cwd=transform_path, check=True)
    subprocess.run(["git", "checkout", "-b", BRANCH_NAME], cwd=transform_path, check=True)

def run_git_commit_and_push(transform_path):
    subprocess.run(["git", "add", "."], cwd=transform_path, check=True)
    subprocess.run(["git", "commit", "-m", "Consolidate dbt source into transform"], cwd=transform_path, check=True)
    subprocess.run(["git", "push", "-u", "origin", BRANCH_NAME], cwd=transform_path, check=True)

# --- Ref map and replacements ---
def build_ref_map_from_vars(var_keys, package_name):
    return {
        k: f"stg_{package_name}__{k}" for k in var_keys
    }

def replace_vars_with_refs_in_models(models_root, ref_map):
    print(f"🔁 Replacing vars using keys: {list(ref_map.keys())}")
    for root, _, files in os.walk(models_root):
        if "staging" in root.split(os.sep):
            continue
        for file in files:
            if file.endswith(".sql"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()

                original = content

                for var_name, ref_model in ref_map.items():
                    pattern = r"\{\{\s*var\(\s*['\"]" + re.escape(var_name) + r"['\"]\s*\)\s*\}\}"
                    content = re.sub(pattern, f"{{{{ ref('{ref_model}') }}}}", content)

                content = content.replace("'{{", "{{").replace("}}'", "}}")

                if content != original:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"📝 Updated: {file_path}")

# --- Main ---
def main(dry_run=False):
    packages = load_package_list(YAML_LIST_PATH)
    creds = load_credentials(CRED_PATH)

    username = creds["username"]
    token = creds["access_token"]

    os.makedirs(PACKAGE_ROOT, exist_ok=True)

    for repo in packages:
        base_name = repo.replace("dbt_", "")
        transform_repo = f"dbt_{base_name}"
        source_repo = f"dbt_{base_name}_source"
        package_path = os.path.join(PACKAGE_ROOT, base_name)
        transform_path = os.path.join(package_path, transform_repo)
        source_path = os.path.join(package_path, source_repo)

        if os.path.exists(package_path):
            shutil.rmtree(package_path)
        os.makedirs(package_path)

        print(f"\n🔄 Consolidating: {base_name}")
        try:
            clone_repo(transform_repo, transform_path, username, token)
            clone_repo(source_repo, source_path, username, token)

            run_git_branch_setup(transform_path)

            changed, var_keys = consolidate_dbt_package(
                package_root=package_path,
                transform_name=transform_repo,
                source_name=source_repo
            )

            ref_map = build_ref_map_from_vars(var_keys, base_name)
            replace_vars_with_refs_in_models(os.path.join(transform_path, "models"), ref_map)

            if changed and not dry_run:
                run_git_commit_and_push(transform_path)
                print(f"🚀 Pushed changes to {BRANCH_NAME} for {transform_repo}")
            elif changed and dry_run:
                print(f"🧪 DRY RUN: Changes detected in {transform_repo}, but not committed.")
            else:
                print(f"✅ No changes needed for {transform_repo}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Git error for {transform_repo}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error for {transform_repo}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without committing or pushing")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
