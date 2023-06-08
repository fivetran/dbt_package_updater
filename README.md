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

#### Set Pull Request Checklist/Body
todo

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

### Versioning Configs (WIP)
#### Set Version Bump Type
What kind of release will these changes produce with our `major`.`minor`.`patch` syntax?
```yml
version-bump-type: <major, minor, or patch>
```

#### Update Required dbt Version (WIP) 🚧 
see if i can fix

#### Update Fivetran_utils dependency version (WIP) 🚧 
see if i can fix
### Actual Code Change Configs
So what changes are we trying to roll out to these packages anyways?

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
#### Adding Code _to_ Files

#### Find and Replace Values



## Step 4: Run the Script
- Update the `package_manager.yml` for all packages you wish to perform the updates on. To be on the safe side of API limits, you may need to only run the script on a subset of data at a time. In other words, you will need to comment out packages and run the updater on about 10 a time.
- If you have already run the script on a repository on some repos and want to re-run it on those some repositories, you will need to remove the `repositories` directory that gets created locally. At the very least, you will need to remove the specific package repos you are re-running the script on from the `repositories` folder.


This is the command you will run in your virual env to run the script:
```bash
python3 main.py 
```

## PR Configurations

### Creating a PR checklist  ([source](pull_request_lib.py))
You can navigate to `open_pull_request()` and update "body" with your checklist. The list needs to be a one-liner or else the formatting gets thrown off. Include `\n`'s to format it nicely. 

## Configuring the changes we are rolling out


### Adding _to_ Files ([source](package_updates.py))
To add to files, navigate to the main function and add a call to this function:
```python
package_updates.add_to_file(file_paths=['files_i_want_to_add_the_same_thing_to',..], new_line='fun new line of code', path_to_repository=path_to_repository, insert_at_top=False/True)
```

### Finding and Replacing Values ([source](package_updates.py))
To find and replace certain values, for example, you will need to:

1. Update your `find-and-replace-ldictist` values inside your `package_manager.yml` file to include all the values you wish to replace.
```yml
find-and-replace-dict:
- find: find_this
  replace: replace_with_this
```
2. Add a call to the `find_and_replace()` function in `main()`
```python
package_updates.find_and_replace(file_paths=file_paths, find_and_replace_dict=config['find-and-replace-dict'], path_to_repository=path_to_repository)
```

### 🚧 Updating packages.yml (Big WIP) 🚧 ([source](package_updates.py))
Currently, this function does not perform as easily as desired. Will need to be updated. The intention is to update all `packages.yml` files such that a new version bump is incorporated for relevant packages without having to specify specific package versions for all packages (current implementation).

### 🚧 Updating dbt_project.yml (Big WIP) 🚧 ([source](package_updates.py))
Currently, this function does not perform as consistently as desired. Will need to be updated. The intention is to update all `dbt_project.yml` (root project and /integration_tests) for a minor/major version bump. In the last roll out, we discovered that this wasn't working for roughly half our packages. 