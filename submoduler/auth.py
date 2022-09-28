import os


git_ssh_identity_file = os.path.expanduser('~/.ssh/id_ed25519')  # TODO: support different location with env.
git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file
