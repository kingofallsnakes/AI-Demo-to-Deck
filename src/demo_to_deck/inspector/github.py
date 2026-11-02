"""Fetch and inspect public GitHub repositories without authentication."""

from __future__ import annotations

import io
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from .local import inspect_local_path

GITHUB_REPO_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


class PrivateOrInaccessibleRepoError(PermissionError):
    """Raised when a repository is private or cannot be accessed anonymously."""


def parse_github_url(url: str) -> tuple[str, str]:
    cleaned = url.strip().rstrip("/")
    match = GITHUB_REPO_RE.match(cleaned)
    if not match:
        # Allow owner/repo shorthand
        parts = cleaned.split("/")
        if len(parts) == 2 and all(parts):
            return parts[0], parts[1].removesuffix(".git")
        raise ValueError(
            "Expected a public GitHub URL like https://github.com/owner/repo "
            "or shorthand owner/repo."
        )
    return match.group("owner"), match.group("repo")


def _api_headers() -> dict[str, str]:
    # Unauthenticated public API access only — never send tokens from this app.
    return {
        "Accept": "application/vnd.github+json",
        "User-Agent": "demo-to-deck-inspector",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def check_repo_is_public(owner: str, repo: str, timeout: float = 20.0) -> dict[str, Any]:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(api, headers=_api_headers(), timeout=timeout)
    if response.status_code == 404:
        raise PrivateOrInaccessibleRepoError(
            f"Repository {owner}/{repo} was not found or is private. "
            "This tool only inspects public repositories and never uses account credentials."
        )
    if response.status_code == 403:
        raise PrivateOrInaccessibleRepoError(
            f"GitHub denied access to {owner}/{repo} (rate limit or permissions). "
            "Try again later or inspect a local clone instead."
        )
    response.raise_for_status()
    data = response.json()
    if data.get("private"):
        raise PrivateOrInaccessibleRepoError(
            f"Repository {owner}/{repo} is private. Private repos are not supported."
        )
    return data


def download_public_zipball(owner: str, repo: str, default_branch: str, dest: Path, timeout: float = 60.0) -> Path:
    """Download the public source zipball and extract it into dest."""
    url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{default_branch}"
    response = requests.get(url, headers={"User-Agent": "demo-to-deck-inspector"}, timeout=timeout)
    if response.status_code == 404:
        # Fallback to API zipball URL
        url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{default_branch}"
        response = requests.get(url, headers=_api_headers(), timeout=timeout)
    if response.status_code in {401, 403, 404}:
        raise PrivateOrInaccessibleRepoError(
            f"Could not download {owner}/{repo}. It may be private or the default branch is unavailable."
        )
    response.raise_for_status()

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(dest)
    # GitHub zip extracts to owner-repo-sha/
    children = [p for p in dest.iterdir() if p.is_dir()]
    if not children:
        raise RuntimeError("Downloaded archive did not contain a project folder.")
    return children[0]


def fetch_public_github_repo(url: str, work_dir: str | Path | None = None) -> dict[str, Any]:
    """
    Download a public GitHub repo snapshot and run static inspection.

    Does not authenticate. Does not execute repository code.
    """
    owner, repo = parse_github_url(url)
    meta = check_repo_is_public(owner, repo)
    branch = meta.get("default_branch") or "main"

    cleanup = False
    if work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="demo_to_deck_gh_"))
        cleanup = True
    else:
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

    extracted: Path | None = None
    try:
        extracted = download_public_zipball(owner, repo, branch, Path(work_dir) / "extract")
        payload = inspect_local_path(extracted)
        payload["source_type"] = "github"
        payload["source_path"] = f"https://github.com/{owner}/{repo}"
        payload["name"] = meta.get("name") or repo
        payload["github"] = {
            "owner": owner,
            "repo": repo,
            "default_branch": branch,
            "description": meta.get("description") or "",
            "stars": meta.get("stargazers_count"),
            "language": meta.get("language"),
            "homepage": meta.get("homepage") or "",
            "topics": meta.get("topics") or [],
        }
        if meta.get("description"):
            payload["readme_sections"] = {
                **payload.get("readme_sections", {}),
                "github_description": meta["description"],
            }
        return payload
    finally:
        if cleanup and work_dir and Path(work_dir).exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def is_probably_github_url(value: str) -> bool:
    value = value.strip()
    if GITHUB_REPO_RE.match(value):
        return True
    if "/" in value and " " not in value and not Path(value).exists():
        parsed = urlparse(value if "://" in value else f"https://{value}")
        return "github.com" in (parsed.netloc or value)
    return False
