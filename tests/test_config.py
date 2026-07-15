from __future__ import annotations

from pathlib import Path

from lazybooks.config import load_libraries, rewrite_remote, select_library


def test_load_libraries_from_config(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
default = "tech"
cache = "~/lazybooks-cache"
remote = "personal-onedrive:"
local_prefix = "~/OneDrive/"

[libraries.assurance]
name = "Assurance"
index_dir = "~/book-indexes/assurance"
index_remote = "personal-onedrive:Library/book-indexes/assurance"

[libraries.tech]
name = "Tech"
index_dir = "~/book-indexes/tech"
index_remote = "personal-onedrive:Library/book-indexes/tech"
"""
    )

    libraries, default_index = load_libraries(config)

    assert [library.key for library in libraries] == ["assurance", "tech"]
    assert libraries[default_index].key == "tech"
    assert select_library(libraries, default_index, None).key == "tech"
    assert select_library(libraries, default_index, "assurance").name == "Assurance"
    assert select_library(libraries, default_index, "missing") is None


def test_rewrite_remote() -> None:
    assert rewrite_remote("old:Library/books", "old:", "new:") == "new:Library/books"
    assert rewrite_remote("other:Library/books", "old:", "new:") == "other:Library/books"
