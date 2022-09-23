from dataclasses import dataclass
from typing import Optional

from git import Repo


@dataclass
class RepoMeta:
    """Metadata class for a repository."""
    name: Optional[str]
    path: Optional[str]
    to_latest_revision: Optional[bool]
    repo: Optional[Repo]
