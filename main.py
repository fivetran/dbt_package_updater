from github import Github
import yaml
import hashlib
import time

hash = hashlib.sha1()
hash.update(str(time.time()).encode("utf-8"))
branch_name = "MagicBot_" + hash.hexdigest()[:10]

body = """
#### This pull request was created automatically 🎉

Before merging this PR:
   - [ ] Verify that all the tests pass.
   - [ ] Tag a release 
"""

with open("credentials.yml") as file:
    creds = yaml.load(file, Loader=yaml.FullLoader)

g = Github(creds["access_token"])

with open("package_manager.yml") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

for repo in config["repositories"]:
    repo = g.get_repo("Fivetran/" + repo)
    content = repo.get_contents("packages.yml")
    packages = yaml.load(content.decoded_content, Loader=yaml.FullLoader)

    for package in packages["packages"]:
        name = package["package"]
        if name in config["packages"]:
            package["version"] = config["packages"][name]

    new_packages = yaml.dump(packages, encoding="utf-8")

    master_sha = repo.get_branch(branch="master").commit.sha
    repo.create_git_ref(ref="refs/heads/" + branch_name, sha=master_sha)

    repo.update_file(
        path=content.path,
        message="Updating package dependendcies - test",
        content=new_packages,
        sha=content.sha,
        branch=branch_name,
    )

    repo.create_pull(
        title="[MagicBot] Bumping package version",
        body=body,
        head=branch_name,
        base="master",
    )
