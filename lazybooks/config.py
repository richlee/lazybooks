from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


DEFAULT_CONFIG = Path(os.environ.get("LAZYBOOKS_CONFIG", "~/.config/lazybooks/config.toml")).expanduser()


@dataclass(frozen=True)
class LibraryConfig:
    key: str
    name: str
    manifest: Path
    index_dir: Path
    index_remote: str
    cache: Path
    remote: str
    local_prefix: str


def expand_path(value: str) -> Path:
    return Path(value).expanduser()


def demo_root() -> Path:
    return Path(str(resources.files("lazybooks.demo")))


def local_prefix(value: str) -> str:
    expanded = str(expand_path(value))
    return expanded if expanded.endswith("/") else expanded + "/"


def fallback_library() -> list[LibraryConfig]:
    index_dir = expand_path(os.environ.get("LAZYBOOKS_INDEX_DIR", "~/book-indexes/assurance"))
    manifest = expand_path(os.environ.get("LAZYBOOKS_MANIFEST", str(index_dir / "manifest.json")))
    remote = os.environ.get("LAZYBOOKS_REMOTE", "onedrive:")
    index_remote = os.environ.get("LAZYBOOKS_INDEX_REMOTE", f"{remote}Library/book-indexes/assurance")
    return [
        LibraryConfig(
            key="assurance",
            name=os.environ.get("LAZYBOOKS_TITLE", "Assurance"),
            manifest=manifest,
            index_dir=index_dir,
            index_remote=index_remote,
            cache=expand_path(os.environ.get("LAZYBOOKS_CACHE", "~/book-cache")),
            remote=remote,
            local_prefix=local_prefix(os.environ.get("LAZYBOOKS_LOCAL_PREFIX", "~/OneDrive/")),
        )
    ]


def rewrite_remote(remote_path: str, old_remote: str, new_remote: str) -> str:
    if old_remote != new_remote and remote_path.startswith(old_remote):
        return new_remote + remote_path[len(old_remote) :]
    return remote_path


def load_libraries(config_path: str | Path | None = DEFAULT_CONFIG) -> tuple[list[LibraryConfig], int]:
    config_path = expand_path(str(config_path)) if config_path is not None else DEFAULT_CONFIG
    if not config_path.exists():
        return fallback_library(), 0

    config_text = config_path.read_text().replace("{demo_root}", demo_root().as_posix())
    data = tomllib.loads(config_text)
    default_key = str(data.get("default", ""))
    global_cache = str(data.get("cache", os.environ.get("LAZYBOOKS_CACHE", "~/book-cache")))
    configured_remote = str(data.get("remote", "onedrive:"))
    global_remote = os.environ.get("LAZYBOOKS_REMOTE", configured_remote)
    global_prefix = str(data.get("local_prefix", os.environ.get("LAZYBOOKS_LOCAL_PREFIX", "~/OneDrive/")))
    library_data = data.get("libraries", {})
    if not isinstance(library_data, dict) or not library_data:
        return fallback_library(), 0

    libraries: list[LibraryConfig] = []
    for key, values in library_data.items():
        if not isinstance(values, dict):
            continue
        index_dir = expand_path(str(values.get("index_dir", f"~/book-indexes/{key}")))
        manifest = expand_path(str(values.get("manifest", str(index_dir / "manifest.json"))))
        library_remote = os.environ.get("LAZYBOOKS_REMOTE", str(values.get("remote", global_remote)))
        configured_library_remote = str(values.get("remote", configured_remote))
        index_remote = rewrite_remote(str(values.get("index_remote", "")), configured_library_remote, library_remote)
        libraries.append(
            LibraryConfig(
                key=str(key),
                name=str(values.get("name", str(key).replace("-", " ").title())),
                manifest=manifest,
                index_dir=index_dir,
                index_remote=index_remote,
                cache=expand_path(str(values.get("cache", global_cache))),
                remote=library_remote,
                local_prefix=local_prefix(str(values.get("local_prefix", global_prefix))),
            )
        )

    if not libraries:
        return fallback_library(), 0
    default_index = next((idx for idx, library in enumerate(libraries) if library.key == default_key), 0)
    return libraries, default_index


def select_library(libraries: list[LibraryConfig], default_index: int, key: str | None) -> LibraryConfig | None:
    if not key:
        return libraries[default_index]
    return next((library for library in libraries if library.key == key), None)
