def update_project(
    repo: github.Repository.Repository, branch_name: str, config: str
) -> None:
    """Updates the dbt_project.yml file."""
    try:
        project_content = find_file_in_repo(repo, "dbt_project.yml")
        project = ruamel.yaml.load(
            project_content.decoded_content,
            Loader=ruamel.yaml.RoundTripLoader,
            preserve_quotes=True,
            )
   
        # Update the require-dbt-version
        project["require-dbt-version"] = config["require-dbt-version"]

        # Update the project file
        repo.update_file(
            path=project_content.path,
            message="Updating require-dbt-version",
            content=ruamel.yaml.dump(project, Dumper=ruamel.yaml.RoundTripDumper),
            sha=project_content.sha,
            branch=branch_name,
        )

    except github.GithubException as github_exception:
        print(github_exception.data["message"])