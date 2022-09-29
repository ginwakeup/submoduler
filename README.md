# submoduler
![Alt text](resources/gh/header.png?raw=true "Submoduler")

An app that iterates a list of repositories and updates each of their submodules to the latest commit.

# TODOs

- [x] Run Process for 1 or more repositories using HTTPS and PAT.
- [ ] Run process for entire organization.
   
## Build the Docker Image

`docker build . -t <tag_here>`

## Run the Docker Image

Pass your `PAT` and Username as environment variables:

`docker run -e PAT=<your_PAT_here> -e USER=<your_username_here> -v <yaml_config_host_path_here>:/opt/submoduler.yaml <tag_here>`

## Run as a Pytho App

Submoduler can be executed as a simple Python App.

Just set `PAT`, `USER` and `EMAIL`(Optional) as environment variables and execute: `submoduler/main.py`.

## Configuration

Submoduler can be configured with a .yaml file which you then mount on the docker container.

Here's an example of a `submoduler.yaml` configuration file:

```yaml
repos:
  test_repo:
    url: https://github.com/<your_user>/<repo_name>.git
    to_latest_revision: true
    init: true
    force_reset: true
    recursive: true
interval: 3
```

- repos: this key contains a dictionary of repositories metadata. Each repository metadata has
  a key which describes the repo name (e.g. test_repo)
  Each repository metadata can have the following keys:
  - **url**: the https url of the repository.
  - **to_latest_revision**: if the submodules need to be updated to the latest revision.
  - **init**: if not initialised, init the submodules.
  - **force_reset**: remove any local change and force reset on the submodules.
  - **recursive**: update the children submodules.
- **interval**: this defines how often the check is performed on your repository submodules in seconds.
