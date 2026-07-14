from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
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


def _expand_path(value: str) -> Path:
    return Path(value).expanduser()


def _local_prefix(value: str) -> str:
    expanded = str(_expand_path(value))
    return expanded if expanded.endswith("/") else expanded + "/"


def _fallback_library() -> list[LibraryConfig]:
    index_dir = _expand_path(os.environ.get("LAZYBOOKS_INDEX_DIR", "~/book-indexes/assurance"))
    manifest = _expand_path(os.environ.get("LAZYBOOKS_MANIFEST", str(index_dir / "manifest.json")))
    remote = os.environ.get("LAZYBOOKS_REMOTE", "onedrive:")
    index_remote = os.environ.get("LAZYBOOKS_INDEX_REMOTE", f"{remote}Library/book-indexes/assurance")
    return [
        LibraryConfig(
            key="assurance",
            name=os.environ.get("LAZYBOOKS_TITLE", "Assurance"),
            manifest=manifest,
            index_dir=index_dir,
            index_remote=index_remote,
            cache=_expand_path(os.environ.get("LAZYBOOKS_CACHE", "~/book-cache")),
            remote=remote,
            local_prefix=_local_prefix(os.environ.get("LAZYBOOKS_LOCAL_PREFIX", "~/OneDrive/")),
        )
    ]


def load_libraries(config_path: Path = DEFAULT_CONFIG) -> tuple[list[LibraryConfig], int]:
    if not config_path.exists():
        return _fallback_library(), 0

    data = tomllib.loads(config_path.read_text())
    default_key = str(data.get("default", ""))
    global_cache = str(data.get("cache", os.environ.get("LAZYBOOKS_CACHE", "~/book-cache")))
    global_remote = str(data.get("remote", os.environ.get("LAZYBOOKS_REMOTE", "onedrive:")))
    global_prefix = str(data.get("local_prefix", os.environ.get("LAZYBOOKS_LOCAL_PREFIX", "~/OneDrive/")))
    library_data = data.get("libraries", {})
    if not isinstance(library_data, dict) or not library_data:
        return _fallback_library(), 0

    libraries: list[LibraryConfig] = []
    for key, values in library_data.items():
        if not isinstance(values, dict):
            continue
        index_dir = _expand_path(str(values.get("index_dir", f"~/book-indexes/{key}")))
        manifest = _expand_path(str(values.get("manifest", str(index_dir / "manifest.json"))))
        libraries.append(
            LibraryConfig(
                key=str(key),
                name=str(values.get("name", str(key).replace("-", " ").title())),
                manifest=manifest,
                index_dir=index_dir,
                index_remote=str(values.get("index_remote", "")),
                cache=_expand_path(str(values.get("cache", global_cache))),
                remote=str(values.get("remote", global_remote)),
                local_prefix=_local_prefix(str(values.get("local_prefix", global_prefix))),
            )
        )

    if not libraries:
        return _fallback_library(), 0
    default_index = next((idx for idx, library in enumerate(libraries) if library.key == default_key), 0)
    return libraries, default_index
