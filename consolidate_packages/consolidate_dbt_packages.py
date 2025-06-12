# Run consolidate_all.py--NOT this file

import os
import shutil
import yaml
import re

def load_yaml_file(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml_file(path, content):
    with open(path, 'w') as f:
        yaml.dump(content, f, sort_keys=False, width=float("inf"))
    with open(path, 'r') as f:
        raw = f.read()
    raw = raw.replace("''", "'").replace("'{{", '"{{').replace("}}'", '}}"')
    raw = raw.replace(
        '''require-dbt-version:\n- '>=1.3.0'\n- <2.0.0''',
        '''require-dbt-version: [">=1.3.0", "<2.0.0"]'''
    )
    with open(path, 'w') as f:
        f.write(raw)

def copy_folder(src, dst, subfolder, nested_target=None):
    changed = False
    src_path = os.path.join(src, subfolder)
    dst_path = os.path.join(dst, nested_target or subfolder)
    if not os.path.exists(src_path):
        return changed
    for root, _, files in os.walk(src_path):
        rel_root = os.path.relpath(root, src_path)
        target_dir = os.path.join(dst_path, rel_root)
        os.makedirs(target_dir, exist_ok=True)
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(target_dir, file)
            if os.path.exists(dest_file):
                base, ext = os.path.splitext(file)
                dest_file = os.path.join(target_dir, f"{base}_source{ext}")
            shutil.copy2(src_file, dest_file)
            changed = True
    return changed

def consolidate_dbt_package(package_root, transform_name, source_name):
    transform_path = os.path.join(package_root, transform_name)
    source_path = os.path.join(package_root, source_name)

    changed = False

    # 1. Copy models and macros
    if copy_folder(source_path, transform_path, "models", "models/staging"):
        changed = True
    if copy_folder(source_path, transform_path, "macros", "macros/staging"):
        changed = True

    # 2. Copy packages.yml
    source_packages_yml = os.path.join(source_path, "packages.yml")
    transform_packages_yml = os.path.join(transform_path, "packages.yml")
    if os.path.exists(source_packages_yml):
        shutil.copy2(source_packages_yml, transform_packages_yml)
        changed = True

    # 3. Replace dbt_project.yml
    transform_yml = os.path.join(transform_path, "dbt_project.yml")
    source_yml = os.path.join(source_path, "dbt_project.yml")
    transform_original_data = load_yaml_file(transform_yml) if os.path.exists(transform_yml) else {}
    source_data = load_yaml_file(source_yml)

    if os.path.exists(transform_yml):
        os.remove(transform_yml)
    shutil.copy2(source_yml, transform_yml)
    changed = True

    # 4. Merge preserved config
    transform_package = transform_name.replace("dbt_", "")
    source_package = source_name.replace("dbt_", "")
    merged_data = load_yaml_file(transform_yml)

    merged_data.setdefault("models", {})
    merged_data.setdefault("vars", {})

    # Remove models.<source> and models.<transform>
    merged_data["models"].pop(source_package, None)
    merged_data["models"].pop(transform_package, None)

    # Restore other model blocks
    for k, v in transform_original_data.get("models", {}).items():
        if k not in {source_package, transform_package}:
            merged_data["models"][k] = v
            changed = True

    # Re-add models.<transform> with staging
    preserved_model_block = transform_original_data.get("models", {}).get(transform_package, {})
    merged_data["models"][transform_package] = {**preserved_model_block, "staging": {"+materialized": "view"}}
    changed = True

    # Restore vars.<transform>
    transform_vars = transform_original_data.get("vars", {}).get(transform_package, {})
    merged_data["vars"][transform_package] = transform_vars
    save_yaml_file(transform_yml, merged_data)

    ref_keys = list(transform_vars.keys())
    print(f"📦 Returning transform vars for replacement: {ref_keys}")
    return changed, ref_keys
