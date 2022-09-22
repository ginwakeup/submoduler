import unittest
import os
import uuid

from git import Repo, Git

from submoduler import submoduler


class TestsBase(unittest.TestCase):
    TEST_REPO_A_PATH = "../../../test_repo_a"
    TEST_REPO_B_PATH = "../../../test_repo_b"
    README_A_PATH = os.path.abspath(os.path.join(TEST_REPO_A_PATH, "README.md"))
    README_B_A_PATH = os.path.abspath(os.path.join(TEST_REPO_B_PATH, "test_repo_a", "README.md"))
    SM = submoduler.Submoduler([TEST_REPO_B_PATH])

    git_ssh_identity_file = os.path.expanduser('~/.ssh/id_ed25519')  # TODO: support different location with env.
    git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file

    def test_a01_submodule_update(self):
        """Simple test that pushes a change to a repo and checks if its submodule is updated on another repository."""
        # First we cache the content of the test_repo_b/test_repo_a/README.
        with Git().custom_environment(
            GIT_SSH_COMMAND=self.git_ssh_cmd
        ):
            self.REPO_A = Repo(self.TEST_REPO_A_PATH)

            self.REPO_A.git.fetch()

            with open(self.README_A_PATH, "w") as readme_a_file:
                uid = str(uuid.uuid1())
                readme_a_file.write(uid)
            self.REPO_A.index.add(self.README_A_PATH)
            self.REPO_A.index.commit("README unittest change.")
            self.REPO_A.remote().push()

            # Update the submodule.
            self.SM.update_repos()

            with open(self.README_B_A_PATH, "r") as readme_b_file:
                repo_b_repo_a_submodule_readme = readme_b_file.read()

                self.assertEqual(uid, repo_b_repo_a_submodule_readme)


