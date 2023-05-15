# Package Updater

The purpose of this package is to enable the Solutions Analytics team at Fivetran a method to programmatically roll out updates to all Fivetran dbt Packages created and maintained by our team.

## Installation and Usage Instructions

### Setting up your environment
1. Clone this repo and checkout on `main`
2. Set up a local virtual environment
    - Navigate to the location of this cloned repo
    - Create a virtual environment
3. If you already have a preferred approach for creating a Python virtual environment, skip this step. Creating a virtual environment, you can do the below within your cloned repo:
```bash
pip install virtualenv # once 
virtualenv venv # once
source venv/bin/activate # everytime
```
4. Install necessary dependencies:
```bash
pip install -r requirements.txt
```

> If you get conflicting versions errors at this step, you may need to investigate PyPi and update (or rollback) version ranges to algin.

5. (For Fivetran Solutions team) If you are running into errors on installing the `requirements.txt` or other issues with your virtual environment, please try the venv file for this use case in our shared vault.

6. After setting up the below for prerequisites you can start running your script.
    - You will need to remove the `repositories` directory or just the subdirectory pertaining to the repo you are updating for if you are re-running updates for the same repo.
    - Run your script with the below:
    ```bash
    python3 main.py 
    ```

# Using the Package Updater for mass repo updates

## Prerequisites 
- Create a `credentials.yml` file that resembles `samples.credentials.yml`.  
    - You will first need to [create an ssh key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) locally and then add it to your `github/settings/ssh and gpg keys`. Remember to configure SSO and authorize Fivetran. 
    - You will need to create a token in Github. Navigate to `github/settings/developer settings/personal access tokens/tokens classic` and create a new token. Name it clearly. Select the settings you need for this token. Set an expiration. Copy and paste the token into your `credentials.yml` file.

- Update the `package_manager.yml` for all packages you wish to perform the updates on. To be on the safe side of API limits, you may need to only run the script on a subset of data at a time. In other words, you will need to comment out packages and run the updater on about 10 a time.

- If you are creating branches for the first time -- you will need to make sure in `main.py` you set `branch_exists = False`. If you are updating branches that already have changes, you will need to set `branch_exists = True`. 

## Customization
### Setting up Branch Names and Commit Messages
You can update the values in `set_defaults()` to your desired branch name and commit message. 

### Creating a PR checklist
You can navigate to `open_pull_request()` and update "body" with your checklist. The list needs to be a one-liner or else the formatting gets thrown off.

## Features
### Removing Files (source)
To remove files, navigate to the `main` function and find the variable `files_to_remove`. You can update this list with the files' file paths you would like to remove. The path starts from the root directory of the dbt project you are updating. For example, to remove your `integration_tests/requirements.txt` you would declare the `files_to_remove` variable like so:

```python
files_to_remove = ['integration_tests/requirements.txt']
```

### Adding Files
To add files, navigate to the main function and find the variable `files_to_add`. You can update this list with the files' file paths you would like to add. The path starts from the root directory of the dbt project you are updating. You will need to add the files into the `dbt_package_updater/docs` folder under the same structure as the dbt project you are updating. 

For example, if you want to add a new `requirements2.txt` file into your integration test directory on your dbt project you would:

1. Create an `integration_tests` directory within the `docs` directory of this repo. 
2. Add the file `requirements2.txt` into `integration_tests`
3. Delcare your `files_to_add` variable like so:
```python
files_to_add = ['integration_tests/requirements2.txt']
```

### Adding to Files

### Finding and Replacing Values (Minor WIP)
Currently, this function has quite a bit of hard coded logic that will need to be made more flexible. The current function is from the latest migration mass update (dbt utils v1.0 migration + buildkite). 

To find and replace certain values, for example, you will need to:

1. Update your `find-and-replace-list` values inside your `package_manager.yml` file to include all the values you wish to replace. 
2. Update the `find_and_replace()` function in your `main.py` to execute the logic you would like to implement. 

### 🚧 Updating packages.yml (Big WIP) 🚧
Currently, this function does not perform as easily as desired. Will need to be updated. The intention is to update all `packages.yml` files such that a new version bump is incorporated for relevant packages without having to specify specific package versions for all packages (current implementation).

### 🚧 Updating dbt_project.yml (Big WIP) 🚧
Currently, this function does not perform as consistently as desired. Will need to be updated. The intention is to update all `dbt_project.yml` (root project and integration_tests) for a minor/major version bump. In the last roll out, we discovered that this wasn't working for roughly half our packages. 







