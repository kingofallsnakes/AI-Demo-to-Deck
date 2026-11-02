"""Static filesystem scanning helpers — reads files, never executes them."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Skip bulky / sensitive trees during inspection.
SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "coverage",
    ".next",
    "target",
    "vendor",
}

DOC_NAMES = {
    "readme",
    "readme.md",
    "readme.rst",
    "readme.txt",
    "contributing.md",
    "changelog.md",
    "license",
    "license.md",
}

MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "composer.json",
    "gemfile",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "makefile",
    "streamlit",
    "app.py",
    "main.py",
    "index.html",
    "index.js",
    "index.ts",
    "index.tsx",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".toml",
    ".yml",
    ".yaml",
    ".html",
    ".css",
    ".sh",
    ".bat",
    ".ps1",
    ".rb",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cs",
    ".php",
    ".sql",
    ".ini",
    ".cfg",
    ".env.example",
}

MAX_FILE_BYTES = 200_000
MAX_FILES = 400


def safe_read_text(path: Path, limit: int = MAX_FILE_BYTES) -> str:
    try:
        data = path.read_bytes()[:limit]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    root = root.resolve()
    for path in root.rglob("*"):
        if len(files) >= MAX_FILES:
            break
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name.lower() not in DOC_NAMES:
            # Still keep known manifests without extensions of interest
            if path.name.lower() not in MANIFEST_NAMES:
                continue
        files.append(path)
    return files


def find_readme(root: Path) -> tuple[str, str]:
    candidates = [
        "README.md",
        "Readme.md",
        "readme.md",
        "README.rst",
        "README.txt",
        "README",
    ]
    for name in candidates:
        path = root / name
        if path.is_file():
            return str(path.relative_to(root)), safe_read_text(path)
    # Case-insensitive fallback
    for path in root.iterdir() if root.is_dir() else []:
        if path.is_file() and path.name.lower().startswith("readme"):
            return str(path.relative_to(root)), safe_read_text(path)
    return "", ""


def detect_stack_signals(root: Path, files: list[Path]) -> dict[str, Any]:
    names = {p.name.lower() for p in files}
    rels = {str(p.relative_to(root)).replace("\\", "/").lower() for p in files}
    signals: dict[str, Any] = {
        "languages": [],
        "frameworks": [],
        "package_managers": [],
        "has_tests": False,
        "has_docker": False,
        "entry_hints": [],
    }

    if any(n.endswith(".py") for n in names) or "pyproject.toml" in names or "requirements.txt" in names:
        signals["languages"].append("Python")
    if any(n.endswith(ext) for n in names for ext in (".js", ".ts", ".tsx", ".jsx")) or "package.json" in names:
        signals["languages"].append("JavaScript/TypeScript")
    if "go.mod" in names or any(n.endswith(".go") for n in names):
        signals["languages"].append("Go")
    if "cargo.toml" in names:
        signals["languages"].append("Rust")
    if any(n.endswith(".java") for n in names) or "pom.xml" in names:
        signals["languages"].append("Java")

    if "streamlit" in " ".join(rels) or any("import streamlit" in safe_read_text(p)[:2000] for p in files if p.suffix == ".py"):
        signals["frameworks"].append("Streamlit")
    if "package.json" in names:
        signals["package_managers"].append("npm/yarn/pnpm")
        pkg = root / "package.json"
        if pkg.is_file():
            try:
                data = json.loads(safe_read_text(pkg))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for key, label in (
                    ("react", "React"),
                    ("next", "Next.js"),
                    ("vue", "Vue"),
                    ("express", "Express"),
                    ("fastapi", "FastAPI"),
                ):
                    if key in deps:
                        signals["frameworks"].append(label)
                scripts = data.get("scripts", {})
                if scripts:
                    signals["entry_hints"].append(f"npm scripts: {', '.join(list(scripts)[:8])}")
            except json.JSONDecodeError:
                pass
    if "requirements.txt" in names or "pyproject.toml" in names:
        signals["package_managers"].append("pip/poetry")
    if "dockerfile" in names or "docker-compose.yml" in names or "docker-compose.yaml" in names:
        signals["has_docker"] = True
        signals["frameworks"].append("Docker")

    if any("test" in str(p).lower() for p in files):
        signals["has_tests"] = True

    for hint in ("app.py", "main.py", "index.html", "manage.py", "server.js"):
        if hint in names:
            signals["entry_hints"].append(hint)

    # Deduplicate while preserving order
    for key in ("languages", "frameworks", "package_managers", "entry_hints"):
        seen: set[str] = set()
        ordered: list[str] = []
        for item in signals[key]:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
        signals[key] = ordered
    return signals


def extract_readme_sections(readme: str) -> dict[str, str]:
    """Split markdown-ish README into heading -> body sections."""
    if not readme.strip():
        return {}
    sections: dict[str, str] = {}
    current = "intro"
    buf: list[str] = []
    for line in readme.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            sections[current] = "\n".join(buf).strip()
            current = re.sub(r"^#{1,3}\s+", "", line).strip().lower()
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf).strip()
    return {k: v for k, v in sections.items() if v}


def extract_bullet_lines(text: str, limit: int = 12) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^[-*+]\s+", stripped) or re.match(r"^\d+[.)]\s+", stripped):
            cleaned = re.sub(r"^([-*+]|\d+[.)])\s+", "", stripped).strip()
            if cleaned:
                bullets.append(cleaned)
        if len(bullets) >= limit:
            break
    return bullets


def summarize_key_files(root: Path, files: list[Path], limit: int = 20) -> list[dict[str, str]]:
    interesting: list[Path] = []
    priority = list(MANIFEST_NAMES) + ["readme.md", "app.py", "main.py"]
    for name in priority:
        for path in files:
            if path.name.lower() == name and path not in interesting:
                interesting.append(path)
    for path in files:
        if path not in interesting and path.suffix in {".py", ".md", ".ts", ".tsx", ".js"}:
            interesting.append(path)
        if len(interesting) >= limit:
            break

    summaries: list[dict[str, str]] = []
    for path in interesting[:limit]:
        rel = str(path.relative_to(root)).replace("\\", "/")
        role = "documentation" if path.name.lower().startswith("readme") else "source"
        if path.name.lower() in MANIFEST_NAMES:
            role = "manifest"
        excerpt = safe_read_text(path, 800).strip().replace("\r\n", "\n")
        summaries.append({"path": rel, "role": role, "excerpt": excerpt[:500]})
    return summaries
