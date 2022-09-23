import os
import time
import threading

from urllib.request import urlopen

from git import Repo
from loguru import logger
from dacite import from_dict

from repo_meta import RepoMeta


class Submoduler:
    """Core class with the only responsibility to parse repositories and perform the Git Operations."""
    def __init__(self, configuration: dict):
        """Init.

        Args:
            configuration: a dictionary configuration object.
                The configuration can contain the following keys:
                    - repos: a list of repos. Each entry in repos could be:
                        - a local git repository.
                        - a git URL. In this case, the tool pulls the repository in a temp location.
                        - a root directory in which live multiple git repositories. The tool will iterate all of them and
                        update their submodules.
                    - interval: in seconds, what's the scan/update interval.
        """
        self._interval = configuration.get("interval")
        logger.info(f"Interval set to {self._interval}")

        self._repos_paths = configuration.get("repos")
        self._repos: list[RepoMeta] = []
        self._parse_repos()
        self._start()

    def _parse_repos(self):
        """Parse repositories listed in the configuration and populate self._repos GitPython Repo objects."""
        for repo_name, repo_meta in self._repos_paths.items():
            repo_path = repo_meta.get("path")
            if os.path.isdir(repo_path):
                repo = Repo(repo_path)
                repo_name = repo.working_tree_dir.split("/")[-1]
                repo_meta_class = from_dict(RepoMeta, repo_meta)
                repo_meta_class.name = repo_name
                repo_meta_class.repo = repo

                self._repos.append(repo_meta_class)
                continue

            # Not a local path, check if it's a URL
            try:
                # TODO: complete implementation for URLs.
                urlopen(repo_path)
                self._repos.append(Repo(repo_path))
                continue

            except ValueError:
                pass

            # Not a URL, unknown format.
            logger.warning(f"Couldn't recognize a format for path: {repo_path}")

    def _start(self):
        """Starts a thread for each repository to update its submodules."""
        for repo in self._repos:
            thread = threading.Thread(target=self._update_repo, args=(repo,), daemon=True)
            thread.start()
            thread.join()

    def _update_repo(self, repo_meta: RepoMeta):
        """Performs the update operation on the repository submodules.

        Args:
            repo_meta: RepoMeta object to update.
        """
        while True:
            repo_meta.repo.submodule_update(to_latest_revision=True)
            logger.info(f"Submodules updated for {repo_meta.name}")
            time.sleep(self._interval)
