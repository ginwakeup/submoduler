import os
import time
import threading
import subprocess
import traceback
import requests

import git

from git import Repo
from loguru import logger
from dacite import from_dict

from repo_meta import RepoMeta


class Submoduler:
    """Core class with the only responsibility to parse repositories and perform the Git Operations."""
    _CACHE_DIR = os.path.join(os.path.expanduser("~/"), "submoduler", "repos")
    _GH_API_URL = " https://api.github.com"

    def __init__(self, configuration: dict, user: str, pat: str, email: str):
        """Init.

        Args:
            configuration: a dictionary configuration object.
                The configuration can contain the following keys:
                    - repos: a list of repos as https URL.
                    - interval: in seconds, what's the scan/update interval.
            user: username used for committing submodules updates.
            pat: user PAT.
            email: user email.
        """
        if pat is None:
            raise Exception("No PAT defined.")

        if user is None:
            raise Exception("No Username defined.")

        self._user = user
        self._pat = pat
        self._set_credentials(user, email, pat)

        self._interval = configuration.get("interval")
        logger.info(f"Interval set to {self._interval}")

        self._repos_configs = configuration.get("repos", {})
        self._organization = configuration.get("organization", {})
        if len(self._organization) > 1:
            error = "Only one Organization is supported at this time. Picking the first and discarding the others."
            logger.error(error)
            raise Exception(error)

        self._repos: list[RepoMeta] = []
        os.makedirs(self._CACHE_DIR, exist_ok=True)

        self._parse_repos()
        self._start()

    def _set_credentials(self, user: str, email: str, pat: str):
        """Performs some initial setup for git config to store PAT in git-credentials.

        Args:
            user: username.
            email: user email.
            pat: user pat.
        """
        subprocess.call(["git"] + ["config", "--global", "credential.helper", "store"])
        subprocess.call(["git"] + ["config", "--global", "user.name", user])
        subprocess.call(["git"] + ["config", "--global", "user.email", email])
        with open(os.path.join(os.path.expanduser("~"), ".git-credentials"), "w") as cred_file:
            cred_file.write(f"https://{user}:{pat}@github.com")

    def _make_repo(self, repo_path: str, repo_meta: dict):
        """Creates a Repo object and appends it to self._repos.

        Args:
            repo_path: path of the repo. can be a URL.
            repo_meta: metadata for the repository. This is used to create a RepoMeta object.
        """
        logger.info(f"Creating repo {repo_path}")
        repo = Repo(repo_path)
        logger.info(f"Initializing submodules for repo: {repo_path}")

        # I have tried submodule.update(init=True, to_latest_revision=True),
        # but for some reason it doesn't pull the submodule files.
        subprocess.call(["git"] + ["submodule", "update", "--init"], cwd=repo_path)

        repo.git.fetch()
        repo.git.pull()

        repo_name = repo.working_tree_dir.split("/")[-1]
        repo_meta_class = from_dict(RepoMeta, repo_meta)
        repo_meta_class.name = repo_name
        repo_meta_class.repo = repo
        repo_meta_class.local_path = repo_path

        self._repos.append(repo_meta_class)

    def _get_org_repos(self, org_name: str) -> list[dict]:
        """Given an organization name, return all its repositories.

        Args:
            org_name: organization name.

        Returns:
            list: list of dict.
        """
        return requests.get(f"{self._GH_API_URL}/orgs/{org_name}/repos", auth=(self._user, self._pat)).json()

    def _clone_repo(self, repo_url, repo_clone_path):
        if repo_url.lower().startswith(("https")):
            try:
                Repo.clone_from(repo_url, repo_clone_path)
            except git.GitCommandError as git_error:
                if "already exists" in git_error.stderr:
                    pass
                else:
                    logger.error(traceback.format_exc())
                    raise Exception(git_error.stderr)

        else:
            # Not a URL, unknown format.
            logger.warning(f"Couldn't recognize a format for url: {repo_url}")

    def _process_repo(self, repo_url: str, repo_clone_path: str, repo_meta: dict):
        """Clones a Repo and creates a RepoMeta object stored in the class.

        Args:
            repo_url: https url of the repository to clone.
            repo_clone_path: local path where the repository should be cloned.
            repo_meta: dictionary of metadata for the RepoMeta object.
        """
        self._clone_repo(repo_url, repo_clone_path)
        self._make_repo(repo_clone_path, repo_meta)

    def _parse_repos(self):
        """Parse repositories listed in the configuration and populates self._repos with RepoMeta objects."""
        for repo_name, repo_meta in self._repos_configs.items():
            repo_clone_path = os.path.join(self._CACHE_DIR, repo_name)
            self._process_repo(repo_meta.get("url"), repo_clone_path, repo_meta)

        for org_name, org_meta in self._organization.items():
            repos = self._get_org_repos(org_name)
            for repo_dict in repos:
                repo_clone_path = os.path.join(self._CACHE_DIR, org_name, repo_dict.get("name"))
                self._process_repo(repo_dict.get("html_url"), repo_clone_path, org_meta)

    def _start(self):
        """Starts a thread for each repository to update its submodules every 'interval' as specified in the configuration."""
        threads = []

        for repo in self._repos:
            thread = threading.Thread(target=self._update_repo, args=(repo,), daemon=True)
            thread.start()
            threads.append(thread)

        [thread.join() for thread in threads]

    def _update_repo(self, repo_meta: RepoMeta):
        """Performs the update operation on the repository submodules.

        Args:
            repo_meta: RepoMeta object to update.
        """
        while True:
            subprocess.call(["git"] + ["submodule", "update", "--remote", "--recursive"],
                            cwd=repo_meta.local_path,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT
                            )

            subprocess.call(["git"] + ["add", "."],
                            cwd=repo_meta.local_path,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT
                            )

            subprocess.call(["git"] + ["commit", "-m", repo_meta.commit_message or "Submoduler update"],
                            cwd=repo_meta.local_path,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT
                            )

            subprocess.call(["git"] + ["push"],
                            cwd=repo_meta.local_path,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT
                            )

            logger.info(f"Submodules updated for {repo_meta.name}")
            time.sleep(self._interval)
