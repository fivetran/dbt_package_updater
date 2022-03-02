# Hooper 

## What is Hooper?

Hooper (dbt-package-updater) is a command line tool that enables dbt developers to automatically update package dependencies and required dbt versions in dbt packages. At Fivetran, it is used every time a dbt or dbt-utils release occurs.

## Installation and Usage Instructions

### 1. Clone this repository

In order to use Hooper, you will need to clone this repository. You can do so using the method of your choosing.

### 2. Set up a local environment

We recommend creating a separate Python virtual environment for Hooper.

 __If you already have a preferred approach for creating a Python virtual environment, you can skip this step!__

Create a Python virtual environment for Hooper. Go into your Hooper repo and execute the below:
```bash
pip install virtualenv
virtualenv env
source env/bin.activate
```

### 3. Install the necessary libraries

Once you've created and activated your virtual environment, run the following to install the necessary dependencies:
```base
pip install -r requirements.txt
```
> **Note**: If you run into any issues, you can try individually installing any failed packages using `python -m pip install pygithub` (or `python3` if the latest version of Python is not your default).
### 4. Set the configurations

In order to update dbt packages, the `package_manager.yml` file needs to be updated with. 

* All the repos to be updated. This is under the `repositories` key. 

### 5. Run Hooper

You've now got everything setup and can run Hooper. To do so, you can run the following command:
```bash
python main.py
```
> **Note**: Some packages will only work with the latest version of Python. If you have multiple, you can specifically run with `python3 main.py`. 

This command will replace old issue templates for all packages in `package_manager.yml`.

Once that is complete, Hooper will open a pull request on each repository and print the URL for the pull request to the terminal. 
