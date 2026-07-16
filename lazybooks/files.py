from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .books import Book, safe_name
from .config import LibraryConfig


def remote_path(book: Book, library: LibraryConfig) -> str:
    if book.remote_path:
        return book.remote_path
    if not book.canonical_path.startswith(library.local_prefix):
        raise ValueError(f"Unsupported path: {book.canonical_path}")
    return library.remote + book.canonical_path[len(library.local_prefix) :]


def cached_path(book: Book, library: LibraryConfig) -> Path:
    return library.cache / library.source_key / library.key / safe_name(book)


def open_file(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def fetch_book(book: Book, library: LibraryConfig) -> Path:
    target = cached_path(book, library)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return target
    subprocess.run(["rclone", "copyto", remote_path(book, library), str(target)], check=True)
    return target
