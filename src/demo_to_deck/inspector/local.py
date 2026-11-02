"""Inspect a user-selected local project directory (static reads only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .filesystem import (
    detect_stack_signals,
    extract_readme_sections,
    find_readme,
    iter_project_files,
    summarize_key_files,
)


def inspect_local_path(path: str | Path) -> dict[str, Any]:
    """
    Statically inspect a local directory.

    Returns a raw inspection payload consumed by the analyzer.
    Never executes project code.
    """
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    readme_rel, readme_text = find_readme(root)
    files = iter_project_files(root)
    signals = detect_stack_signals(root, files)
    sections = extract_readme_sections(readme_text)
    key_files = summarize_key_files(root, files)

    return {
        "name": root.name,
        "source_type": "local",
        "source_path": str(root),
        "readme_path": readme_rel,
        "readme_text": readme_text,
        "readme_sections": sections,
        "file_count": len(files),
        "relative_files": [str(p.relative_to(root)).replace("\\", "/") for p in files[:200]],
        "signals": signals,
        "key_files": key_files,
        "warnings": [],
    }
