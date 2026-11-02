"""Repository inspection (static analysis only by default)."""

from .github import fetch_public_github_repo
from .local import inspect_local_path

__all__ = ["inspect_local_path", "fetch_public_github_repo"]
