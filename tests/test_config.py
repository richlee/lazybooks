from __future__ import annotations

from pathlib import Path

from lazybooks.config import (
    cache_home,
    config_home,
    data_home,
    default_book_cache,
    default_index_dir,
    demo_root,
    load_libraries,
    load_sources,
    rewrite_remote,
    select_library,
)


def test_default_paths_use_xdg_locations(monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/lazybooks-config")
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/lazybooks-data")
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/lazybooks-cache")

    assert config_home() == Path("/tmp/lazybooks-config/lazybooks")
    assert data_home() == Path("/tmp/lazybooks-data/lazybooks")
    assert cache_home() == Path("/tmp/lazybooks-cache/lazybooks")
    assert default_index_dir("tech") == Path("/tmp/lazybooks-data/lazybooks/indexes/tech")
    assert default_book_cache() == Path("/tmp/lazybooks-cache/lazybooks/books")


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


def test_load_sources_from_grouped_config(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
default_source = "google"
default_library = "personal"
cache = "~/lazybooks-cache"

[sources.onedrive]
name = "OneDrive"
remote = "personal-onedrive:"
local_prefix = "~/OneDrive/"

[sources.onedrive.libraries.assurance]
name = "Assurance"
index_dir = "~/book-indexes/onedrive/assurance"
index_remote = "personal-onedrive:Library/book-indexes/assurance"

[sources.google]
name = "Google Drive"
remote = "google-drive:"
local_prefix = "~/Google Drive/"

[sources.google.libraries.personal]
name = "Personal"
index_dir = "~/book-indexes/google/personal"
index_remote = "google-drive:Library/book-indexes/personal"
"""
    )

    sources, default_source_index, default_library_index = load_sources(config)
    libraries, default_index = load_libraries(config)

    assert [source.key for source in sources] == ["onedrive", "google"]
    assert sources[default_source_index].key == "google"
    assert sources[default_source_index].libraries[default_library_index].key == "personal"
    assert sources[0].libraries[0].source_name == "OneDrive"
    assert sources[1].libraries[0].remote == "google-drive:"
    assert [library.key for library in libraries] == ["assurance", "personal"]
    assert libraries[default_index].source_key == "google"


def test_grouped_config_default_index_dirs_are_source_scoped(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    config = tmp_path / "config.toml"
    config.write_text(
        """
[sources.onedrive]
remote = "personal-onedrive:"

[sources.onedrive.libraries.assurance]
name = "Assurance"

[sources.google]
remote = "google-drive:"

[sources.google.libraries.assurance]
name = "Assurance"
"""
    )

    sources, _default_source_index, _default_library_index = load_sources(config)

    assert sources[0].libraries[0].index_dir == tmp_path / "data/lazybooks/indexes/onedrive/assurance"
    assert sources[1].libraries[0].index_dir == tmp_path / "data/lazybooks/indexes/google/assurance"


def test_rewrite_remote() -> None:
    assert rewrite_remote("old:Library/books", "old:", "new:") == "new:Library/books"
    assert rewrite_remote("other:Library/books", "old:", "new:") == "other:Library/books"


def test_demo_config_loads() -> None:
    libraries, default_index = load_libraries("examples/demo/config.toml")

    assert [library.key for library in libraries] == ["engineering", "personal"]
    assert libraries[default_index].key == "engineering"
    assert libraries[0].manifest.exists()


def test_packaged_demo_config_loads() -> None:
    libraries, default_index = load_libraries(demo_root() / "config.toml")

    assert [library.key for library in libraries] == ["engineering", "personal"]
    assert libraries[default_index].key == "engineering"
    assert libraries[0].manifest.exists()
    assert libraries[0].cache.exists()
