import requests
import json
import yaml

# Function to load yaml files as dictionaries
def load_yml(yml_name) -> dict:
    with open(yml_name) as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents

# Load file with issue source and destination information
issue_data = load_yml('issue_data.yml')
# Define source repo data
source_repo = issue_data['source_repo_name']
source_owner = issue_data['source_owner']
issue_number = issue_data['source_issue_number']
# Creates url for the source issue. 
source_issue_url = f'https://github.com/{source_owner}/{source_repo}/issues/{issue_number}'

# Github API endpoint for retrieving issue data
issue_api_url = f'https://api.github.com/repos/{source_owner}/{source_repo}/issues/{issue_number}'

# Authenticate with Github API using personal access token
creds = load_yml('../credentials.yml')
access_token = creds['access_token']
auth_header = {'Authorization': f'token {access_token}'}

# Retrieve issue data from source repo
response = requests.get(issue_api_url, headers=auth_header)
response_data = json.loads(response.text)
if response.status_code == 200:
    print(f'Issue successfully retrieved from {source_repo}')
else:
    print(f'Error retrieving issue from {source_repo}: {response.text}')

# Define destination repo(s) data
destination_owner = issue_data['destination_owner']
destination_repos = issue_data['destination_repositories']

# Loop over destination repos and create new issues
for dest_repo in destination_repos:
    create_issue_url = f'https://api.github.com/repos/{destination_owner}/{dest_repo}/issues'
    issue_payload = {
        'title': response_data['title'],
        'body': f'*Copied from [{source_owner}/{source_repo} #{issue_number}]({source_issue_url}).*\n\n' 
            + response_data['body'],
        'labels': issue_data['destination_labels']
        # Add any additional fields or modifications as needed
    }
    response = requests.post(create_issue_url, headers=auth_header, json=issue_payload)
    if response.status_code == 201:
        print(f'Issue created in {dest_repo}')
    else:
        print(f'Error creating issue in {dest_repo}: {response.text}')