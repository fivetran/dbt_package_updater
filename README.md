# Hooper 

## What is Hooper?

Hooper is a command line tool that enables dbt developers to automatically update package dependencies and required dbt versions in dbt packages. At Fivetran, it is used every time a dbt or dbt-utils release occurs.

## Installation and Usage Instructions

### 1. Clone this repository

In order to use Hooper, you will need to clone this repository. You can do so using the method of your choosing.

### 2. Set up a local environment

We recommend creating a separate Python virtual environment for Hooper.

NOTE: If you already have a preferred approach for creating a Python virtual environment, you can skip this step!

Create a Python virtual environment for Hooper. If you don't already have a preferred way of doing this, we recommend pyenv-virtualenv. Follow the instructions to install pyenv and pyenv-virtualenv. Then, from the Hooper repository, run the following:
```bash
pyenv virtualenv 3.8 hooper && pyenv local hooper
```

### 3. Install the necessary libraries

Once you've created and activated your virtual environment, run the following to install the necessary dependencies:
```base
pip install -r requirements.txt
```

### 4. Set the configurations

In order to update dbt packages, the `package_manager.yml` file needs to be updated with:

* All the repos to be updated. This is under the `repositories` key. 
* The bounds for the `require-dbt-verion` variable in the `dbt_project.yml` files of each package to be updated. 
* The version of dbt to be used in CircleCI to test the upgrades. This is under the `ci-dbt-version` key. 
* The version of each dependent package should be updated to in all the dbt packages, i.e. dbt-utils, fivetran-utils. 

### 5. Run Hooper

You've now got everything setup and can run Hooper. To do so, you can run the following command:
```bash
python main.py --repo-type source
```
That command will update all the 'source' repositories with the following changes:
* Bump any packages in `packages.yml` to the version(s) set in `package_manager.yml`
* Bump the `require-dbt-version` in `dbt_project.yml` to the version(s) set in `package_manager.yml`
* Bump the installed version of dbt in `integration_tests/requirements.txt` to the version set in `package_manager.yml`

Once that is complete, Hooper will open a pull request on each repository and print the URL for the pull request to the terminal. 
