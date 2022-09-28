import os
import time
import threading
import subprocess

import git

from git import Repo
from loguru import logger
from dacite import from_dict

from repo_meta import RepoMeta


class Submoduler:
    """Core class with the only responsibility to parse repositories and perform the Git Operations."""
    _CACHE_DIR = os.path.join(os.path.expanduser("~/"), "submoduler", "repos")

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
        os.makedirs(self._CACHE_DIR, exist_ok=True)

        self._parse_repos()
        self._start()

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

    def _parse_repos(self):
        """Parse repositories listed in the configuration and populate self._repos GitPython Repo objects."""
        for repo_name, repo_meta in self._repos_paths.items():
            repo_path = repo_meta.get("path")
            if os.path.isdir(repo_path):
                self._make_repo(repo_path, repo_meta)
                continue

            # Not a local path, check if it's a URL
            elif repo_path.lower().startswith(("git@")):
                repo_clone_path = os.path.join(self._CACHE_DIR, repo_name)
                try:
                    Repo.clone_from(repo_path, repo_clone_path)
                except git.GitCommandError as git_error:
                    if "already exists" in git_error.stderr:
                        pass
                    else:
                        raise Exception(git_error.stderr)

                finally:
                    self._make_repo(repo_clone_path, repo_meta)

            else:
                # Not a URL, unknown format.
                logger.warning(f"Couldn't recognize a format for path: {repo_path}")

    def _start(self):
        """Starts a thread for each repository to update its submodules."""
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
