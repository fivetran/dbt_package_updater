import requests
import json
import yaml

def load_yml(yml_name) -> dict:
    with open(yml_name + '.yml') as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents

# GitHub API endpoint to create an issue
api_endpoint = 'https://api.github.com/repos/{}/{}/issues'

# GitHub access token with the appropriate permissions
creds = load_yml('../credentials')
access_token = creds['access_token']
owner = 'fivetran'

# List of repositories to target
repos = load_yml('issue_repositories')
repo_list = repos['repositories']

# Issue details
issue = load_yml('issue')
issue_title = issue['title']
issue_body = issue['body']
issue_labels = issue['labels']

# Loop over the repositories and create the issue in each one
for repo in repo_list:
    # Set the API endpoint with the appropriate owner and repository name
    url = api_endpoint.format(owner, repo)
    
    # Set the request headers with the access token and content type
    headers = {
        'Authorization': f'token {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Set the request body with the issue details
    data = {
        'title': issue_title,
        'body': issue_body,
        'labels': issue_labels
    }
    
    # Make the POST request to create the issue
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    # Check the response status code for errors
    if response.status_code != 201:
        print(f'Error creating issue in {repo}: {response.content}')
