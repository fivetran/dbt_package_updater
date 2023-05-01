import requests
import json
import load_as_dict as loader

# Define source and destination repositories and issue number
source_repo = 'test'
owner = 'fivetran-catfritz'
issue_number = 2

# List of repositories to target
load_repos = loader.load_yml('issue_repositories')
destination_repos = load_repos['repositories']

creds = loader.load_yml('../credentials')
access_token = creds['access_token']

# Github API endpoint for retrieving issue data
issue_api_url = f'https://api.github.com/repos/{owner}/{source_repo}/issues/{issue_number}'

# Authenticate with Github API using personal access token
auth_header = {'Authorization': f'token {access_token}'}

# Retrieve issue data from source repo
response = requests.get(issue_api_url, headers=auth_header)
issue_data = json.loads(response.text)

# Loop over destination repos and create new issues
for dest_repo in destination_repos:
    create_issue_url = f'https://api.github.com/repos/{owner}/{dest_repo}/issues'
    issue_payload = {
        'title': issue_data['title'],
        'body': f'*Copied from issue #{issue_number}.*\n\n' + issue_data['body'],
        'labels': issue_data['labels'],
        # Add any additional fields or modifications as needed
    }
    response = requests.post(create_issue_url, headers=auth_header, json=issue_payload)
    if response.status_code == 201:
        print(f'Issue created in {dest_repo}')
    else:
        print(f'Error creating issue in {dest_repo}: {response.text}')