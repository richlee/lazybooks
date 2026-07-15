from __future__ import annotations

import subprocess
from pathlib import Path


def app_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_version() -> str:
    try:
        return (app_root() / "VERSION").read_text(encoding="utf-8").strip() or "0+unknown"
    except Exception:
        return "0+unknown"


def git_value(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(app_root()), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "unknown"
    return result.stdout.strip() or "unknown"


def version_info() -> tuple[str, str, str]:
    return (
        project_version(),
        git_value("rev-parse", "--short", "HEAD"),
        git_value("show", "-s", "--format=%cs", "HEAD"),
    )


def version_label() -> str:
    version, commit, commit_date = version_info()
    return f"lazybooks {version} ({commit}, {commit_date})"
