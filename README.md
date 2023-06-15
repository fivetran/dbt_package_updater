# Package Updater Installation and Usage Instructions

The purpose of this package is to enable the Solutions Analytics team at Fivetran a method to programmatically roll out updates to all Fivetran dbt Packages created and maintained by our team.

## Step 1: Setting up your Environment
1. Clone this repo and checkout on `main`
2. Navigate to the location of this cloned repo
3. Set up a local virtual environment:

If you already have a preferred approach for creating a Python virtual environment, skip this step. If not, within your cloned repo, run the following:
```bash
pip install virtualenv # once 
virtualenv venv # once
source venv/bin/activate # everytime you want to activate the virtual env
```
4. Install necessary dependencies in your virtual env:
```bash
pip install -r requirements.txt
```

(For Fivetran Solutions team) If you are running into errors on installing the `requirements.txt` or other issues with your virtual environment, please try the venv file for this use case in our team's shared vault. If it's still not working, you may need to investigate PyPi and update (or rollback) version ranges to avoid conflicts.

## Step 2: Setting up Credentials 
- Create a `credentials.yml` file that resembles `samples.credentials.yml`.  
    - You will first need to [create an ssh key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) locally and then add it to your `github/settings/ssh and gpg keys`. Remember to configure SSO and authorize Fivetran. 
    - You will need to create a token in Github. Navigate to `github/settings/developer settings/personal access tokens/tokens classic` and create a new token. Name it clearly. Select the settings you need for this token. Set an expiration. Copy and paste the token into your `credentials.yml` file.

## Step 3: Set Configurations
All configurations should be made in `package_manager.yml`. This entire yml file will be imported into `main.py` as a `config` dictionary. Nothing should be hard-coded in Python files! 

For the following subsections, you will only have to set the respective configs once for your rollout. The only item in `package_manager.yml` you will need to change with each _run_ of the script is the `repositories` attribute. See Step 4 for more details on this. 

### Github Configs
#### Title your PR
In `package_manager.yml`, set the title of the Mass PRs you will be rolling out:
```yml
pull-request-title: 'Some PR Title'
```

#### Create a PR checklist  ([source](pull_request_body.md))
The body of your PR will be pulled from the `pull_request_body.md` file in this repository. Edit it to your liking (and you can Preview it in VSCode with `shift+command+v`) prior to running the script. 

#### Name your Branch
In `package_manager.yml`, name the branch each PR will be made from:
```yml
branch-name: 'MagicBot/this-is-the-name-of-my-branch'
```
> The `MagicBot/` prefix isn't necessary, but recommended to differentiate these PRs from normal ones.

#### Set Commit Message
In `package_manager.yml`, set the commit message you'd like to push these changes with.
```yml
commit-message: 'some commit message'
```

### Actual Code Change Configs
So what changes are we trying to roll out to these packages anyways? If you do not want to run any of the following functions, make sure the relevant `package_manager.yml` config is commented out.

#### Removing Files ([source](package_updates.py))
Update the `files-to-remove` list in `package_manager.yml` with the files' file paths you would like to remove. The path starts from the root directory of the dbt project you are updating. 

For example, to remove `integration_tests/requirements.txt` and the entire `.circleci` folder you would declare the `files_to_remove` variable like so:

```yml
files-to-remove:
- '.circleci/'
- 'integration_tests/requirements.txt.'
```

#### Adding Files ([source](package_updates.py))
To add files, first add the files/folders you would like rolled out to the `files_to_add` folder in this repo. It's okay if there are other files in there you don't want to include.

Next, update the `files-to-add` list in `package_manager.yml` with the paths of the files/folders you added to the repo folder. 

For example, to add `integration_tests/requirements2.txt` and the entire `.buildkite` folder you would declare the `files_to_add` variable like so:

```yml
files-to-add:
- '.buildkite/'
- 'integration_tests/requirements2.txt.'
```

> Question for team: should we change this so that any and all files in the `files_to_add` folder get added? This would remove the need to adjust `package_manager.yml` as well.

#### Adding _to_ Files ([source](package_updates.py))
Currently, the package updater supports adding code _to_ files, either at the start or end of a file. To add new code to package files, configure `files-to-add-to` in `package_manager.yml` as such:

```yml
files-to-add-to:
- file_paths: ['.buildkite/scripts/run_models.sh']
  insert_at_top: false
  new_line: run-operation fivetran_utils.drop_schemas --target "$db"
- file_paths: ['integration_tests/dbt_project.yml', 'dbt_project.yml']
  insert_at_top: true
  new_line: \# look we added a comment \#
```

#### Finding and Replacing Values ([source](package_updates.py))
To find and replace certain values, add the following to `package_manager.yml` file to include all the values you wish to replace.
```yml
find-and-replace:
- find: find_this
  replace: replace_with_this
- find: now_find_this
  replace: replace_with_this_thing
```

### Versioning Configs
How should we adjust the version of the package, any upstream dependencies, and dbt?

#### Set Version Bump Type
What kind of release will these changes produce with our `major`.`minor`.`patch` syntax? Add the following to `package_manager.yml`.
```yml
version-bump-type: <major, minor, or patch>
```
This will be called in the `update_project()` function.

#### 🚧 Update package dependency version(s) (WIP) 🚧 
> This currently does not work as intended. See [issue #22](https://github.com/fivetran/dbt_package_updater/issues/22).

This is intended to update the ranges of package dependencies in each project's `packages.yml` file. It currently only has logic built out to change the version of `fivetran_utils` and _potentially_ a source package (not fully tested).

To update the version of `fivetran_utils` that each package may depend on, add the following to `package_manager.yml`:
```yml
fivetran-utils-version: [">=0.4.0", "<0.5.0"] # or whatever range you want
```

The version ranges of Fivetran source packages will be informed by the `version-bump-type` you set above.

#### 🚧 Update Required dbt Version (WIP) 🚧 
> This currently does not work as intended. See [issue #21](https://github.com/fivetran/dbt_package_updater/issues/21).

The intention here is: To update the required dbt version across packages, add the following to `package_manager.yml`:
```yml
require-dbt-version: [">=1.4.0", "<2.0.0"] # or whatever range you want
```

## Step 4: Run the Script
- Update the `package_manager.yml` for all packages you wish to perform the updates on. To be on the safe side of API limits, you may need to only run the script on a subset of data at a time. In other words, you will need to comment out packages and run the updater on **about 10 a time**.

> Don't like this workflow? Perhaps take a crack at [Issue #19](https://github.com/fivetran/dbt_package_updater/issues/19)...


This is the command you will run in your virual env to run the script:
```bash
python3 main.py 
```