from __future__ import annotations

import subprocess
import sys

from .config import DEFAULT_CONFIG, LibraryConfig


class RefreshError(RuntimeError):
    def __init__(self, library: LibraryConfig, returncode: int, stderr: str) -> None:
        super().__init__(stderr.strip() or f"rclone exited with {returncode}")
        self.library = library
        self.returncode = returncode
        self.stderr = stderr


def rclone_remotes() -> str:
    try:
        result = subprocess.run(["rclone", "listremotes"], check=True, capture_output=True, text=True)
    except Exception:
        return ""
    return result.stdout.strip()


def refresh_library(library: LibraryConfig) -> None:
    if not library.index_remote:
        raise RuntimeError(f"No index_remote configured for {library.name}")
    library.index_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "rclone",
            "copy",
            library.index_remote,
            str(library.index_dir),
            "--filter",
            "+ index.html",
            "--filter",
            "+ manifest.json",
            "--filter",
            "- *",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RefreshError(library, result.returncode, result.stderr)


def report_refresh_error(exc: RefreshError) -> None:
    print(f"Refresh failed for {exc.library.name}.", file=sys.stderr)
    print(f"Tried remote index: {exc.library.index_remote}", file=sys.stderr)
    if "directory not found" in exc.stderr.casefold():
        print("The rclone remote exists, but that index folder is missing.", file=sys.stderr)
        print(f"Create/generate that library index, or remove it from {DEFAULT_CONFIG} for now.", file=sys.stderr)
        return
    remotes = rclone_remotes()
    if remotes:
        print("Available rclone remotes:", file=sys.stderr)
        for remote in remotes.splitlines():
            print(f"  {remote}", file=sys.stderr)
    print(f"Check the rclone remote name in {DEFAULT_CONFIG} or LAZYBOOKS_REMOTE.", file=sys.stderr)
