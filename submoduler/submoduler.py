from git import Repo


class Submoduler:
    """Core class with the only responsibility to parse repositories and perform the Git Operations."""
    def __init__(self, repos: list[str]):
        """Init.

        Args:
            repos: list of repos. This could be:
                - a list of local paths. In this case the file will expect a .git file in the path.
                - a list of URLs for the repos. The tool will clone the repos in a temp location.
                - a directory with git repos living under it. The tool will parse the entire tree to find them.
        """
        self._repos_paths = repos
        self._repos: list[Repo] = []
        self._parse_repos()

    def _parse_repos(self):
        """Parse the repositories used to initialize the class instance and stores git.Repo objects inside self._repos."""
        # TODO: support all cases.
        for repo in self._repos_paths:
            # For the moment we only support local paths.
            self._repos.append(Repo(repo))

    def update_repos(self):
        """Repositories update fuction. When this is executed, the repos are iterated and all the submodules are updated to the latest commit."""
        for repo in self._repos:
            repo.submodule_update(to_latest_revision=True)
