# submoduler
![Alt text](resources/gh/header.png?raw=true "Submoduler")

Managing git submodules can be tricky.
What Submoduler tries to do is a simple management layer that keeps them updated in multiple repositories/organization repositories.

An app that iterates a list of repositories and updates each of their submodules to the latest commit.
   
## Build the Docker Image

`docker build . -t <tag_here>`

## Run the Docker Image

Pull image:
`docker pull ghcr.io/ginwakeup/submoduler:latest`

Run it and pass your `PAT` and Username as environment variables:

`docker run -e PAT=<your_PAT_here> -e USER=<your_username_here> -v <yaml_config_host_path_here>:/opt/submoduler.yaml <tag_here>`

## Run as a Python App

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
- organization: this key can contain a organization name and configuration for submoduler.
  e.g.
  ```yaml
  organization:
    test-org-name:
      to_latest_revision: true
      init: true
      force_reset: true
      recursive: true
  interval: 3
  ```
  When specifying a Organization, all the repos living under it will be pulled and monitored/updated.
  Right now, only one Submoduler Configuration is supported for all the Org repos, and only 1 repo is supported.
- **interval**: this defines how often the check is performed on your repository submodules in seconds.
