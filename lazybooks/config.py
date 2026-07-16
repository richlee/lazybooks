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
    source_key: str = "default"
    source_name: str = "Default"
    root: Path | None = None
    title: str | None = None
    library_name: str | None = None
    category_depth: int = 1
    calibre_metadata_only: bool = False


@dataclass(frozen=True)
class SourceConfig:
    key: str
    name: str
    libraries: list[LibraryConfig]


def expand_path(value: str) -> Path:
    return Path(value).expanduser()


def demo_root() -> Path:
    return Path(str(resources.files("lazybooks.demo")))


def local_prefix(value: str) -> str:
    expanded = str(expand_path(value))
    return expanded if expanded.endswith("/") else expanded + "/"


def fallback_source() -> SourceConfig:
    index_dir = expand_path(os.environ.get("LAZYBOOKS_INDEX_DIR", "~/book-indexes/assurance"))
    manifest = expand_path(os.environ.get("LAZYBOOKS_MANIFEST", str(index_dir / "manifest.json")))
    remote = os.environ.get("LAZYBOOKS_REMOTE", "onedrive:")
    index_remote = os.environ.get("LAZYBOOKS_INDEX_REMOTE", f"{remote}Library/book-indexes/assurance")
    source_name = os.environ.get("LAZYBOOKS_SOURCE_TITLE", "Default")
    return SourceConfig(
        key="default",
        name=source_name,
        libraries=[
            LibraryConfig(
                key="assurance",
                name=os.environ.get("LAZYBOOKS_TITLE", "Assurance"),
                manifest=manifest,
                index_dir=index_dir,
                index_remote=index_remote,
                cache=expand_path(os.environ.get("LAZYBOOKS_CACHE", "~/book-cache")),
                remote=remote,
                local_prefix=local_prefix(os.environ.get("LAZYBOOKS_LOCAL_PREFIX", "~/OneDrive/")),
                source_key="default",
                source_name=source_name,
            )
        ],
    )


def fallback_library() -> list[LibraryConfig]:
    return fallback_source().libraries


def rewrite_remote(remote_path: str, old_remote: str, new_remote: str) -> str:
    if old_remote != new_remote and remote_path.startswith(old_remote):
        return new_remote + remote_path[len(old_remote) :]
    return remote_path


def parse_library(
    key: str,
    values: dict,
    *,
    source_key: str,
    source_name: str,
    default_cache: str,
    configured_remote: str,
    effective_remote: str,
    default_prefix: str,
) -> LibraryConfig:
    index_dir = expand_path(str(values.get("index_dir", f"~/book-indexes/{key}")))
    manifest = expand_path(str(values.get("manifest", str(index_dir / "manifest.json"))))
    name = str(values.get("name", str(key).replace("-", " ").title()))
    library_remote = os.environ.get("LAZYBOOKS_REMOTE", str(values.get("remote", effective_remote)))
    configured_library_remote = str(values.get("remote", configured_remote))
    index_remote = rewrite_remote(str(values.get("index_remote", "")), configured_library_remote, library_remote)
    root_value = values.get("root")
    return LibraryConfig(
        key=str(key),
        name=name,
        manifest=manifest,
        index_dir=index_dir,
        index_remote=index_remote,
        cache=expand_path(str(values.get("cache", default_cache))),
        remote=library_remote,
        local_prefix=local_prefix(str(values.get("local_prefix", default_prefix))),
        source_key=source_key,
        source_name=source_name,
        root=expand_path(str(root_value)) if root_value else None,
        title=str(values.get("title", f"{name} Books")),
        library_name=str(values.get("library_name", name)),
        category_depth=int(values.get("category_depth", 1)),
        calibre_metadata_only=bool(values.get("calibre_metadata_only", False)),
    )


def load_flat_source(data: dict) -> tuple[list[SourceConfig], int, int]:
    default_key = str(data.get("default", ""))
    global_cache = str(data.get("cache", os.environ.get("LAZYBOOKS_CACHE", "~/book-cache")))
    configured_remote = str(data.get("remote", "onedrive:"))
    global_remote = os.environ.get("LAZYBOOKS_REMOTE", configured_remote)
    global_prefix = str(data.get("local_prefix", os.environ.get("LAZYBOOKS_LOCAL_PREFIX", "~/OneDrive/")))
    source_name = str(data.get("source_name", "Default"))
    library_data = data.get("libraries", {})
    if not isinstance(library_data, dict) or not library_data:
        source = fallback_source()
        return [source], 0, 0

    libraries: list[LibraryConfig] = []
    for key, values in library_data.items():
        if not isinstance(values, dict):
            continue
        libraries.append(
            parse_library(
                str(key),
                values,
                source_key="default",
                source_name=source_name,
                default_cache=global_cache,
                configured_remote=configured_remote,
                effective_remote=global_remote,
                default_prefix=global_prefix,
            )
        )

    if not libraries:
        source = fallback_source()
        return [source], 0, 0
    default_index = next((idx for idx, library in enumerate(libraries) if library.key == default_key), 0)
    return [SourceConfig(key="default", name=source_name, libraries=libraries)], 0, default_index


def load_grouped_sources(data: dict) -> tuple[list[SourceConfig], int, int]:
    source_data = data.get("sources", {})
    if not isinstance(source_data, dict) or not source_data:
        source = fallback_source()
        return [source], 0, 0

    default_source_key = str(data.get("default_source", ""))
    default_library_key = str(data.get("default_library", data.get("default", "")))
    global_cache = str(data.get("cache", os.environ.get("LAZYBOOKS_CACHE", "~/book-cache")))
    global_configured_remote = str(data.get("remote", "onedrive:"))
    global_remote = os.environ.get("LAZYBOOKS_REMOTE", global_configured_remote)
    global_prefix = str(data.get("local_prefix", os.environ.get("LAZYBOOKS_LOCAL_PREFIX", "~/OneDrive/")))

    sources: list[SourceConfig] = []
    for source_key, source_values in source_data.items():
        if not isinstance(source_values, dict):
            continue
        source_name = str(source_values.get("name", str(source_key).replace("-", " ").title()))
        source_cache = str(source_values.get("cache", global_cache))
        configured_remote = str(source_values.get("remote", global_configured_remote))
        effective_remote = os.environ.get("LAZYBOOKS_REMOTE", configured_remote)
        source_prefix = str(source_values.get("local_prefix", global_prefix))
        library_data = source_values.get("libraries", {})
        if not isinstance(library_data, dict):
            continue

        libraries: list[LibraryConfig] = []
        for library_key, library_values in library_data.items():
            if not isinstance(library_values, dict):
                continue
            libraries.append(
                parse_library(
                    str(library_key),
                    library_values,
                    source_key=str(source_key),
                    source_name=source_name,
                    default_cache=source_cache,
                    configured_remote=configured_remote,
                    effective_remote=effective_remote,
                    default_prefix=source_prefix,
                )
            )
        if libraries:
            sources.append(SourceConfig(key=str(source_key), name=source_name, libraries=libraries))

    if not sources:
        source = fallback_source()
        return [source], 0, 0

    default_source_index = next((idx for idx, source in enumerate(sources) if source.key == default_source_key), 0)
    default_source = sources[default_source_index]
    default_library_index = next(
        (idx for idx, library in enumerate(default_source.libraries) if library.key == default_library_key),
        0,
    )
    return sources, default_source_index, default_library_index


def load_sources(config_path: str | Path | None = DEFAULT_CONFIG) -> tuple[list[SourceConfig], int, int]:
    config_path = expand_path(str(config_path)) if config_path is not None else DEFAULT_CONFIG
    if not config_path.exists():
        source = fallback_source()
        return [source], 0, 0

    config_text = config_path.read_text().replace("{demo_root}", demo_root().as_posix())
    data = tomllib.loads(config_text)
    if "sources" in data:
        return load_grouped_sources(data)
    return load_flat_source(data)


def load_libraries(config_path: str | Path | None = DEFAULT_CONFIG) -> tuple[list[LibraryConfig], int]:
    sources, default_source_index, default_library_index = load_sources(config_path)
    libraries = [library for source in sources for library in source.libraries]
    default_source = sources[default_source_index]
    default_library = default_source.libraries[default_library_index]
    default_index = next((idx for idx, library in enumerate(libraries) if library is default_library), 0)
    return libraries, default_index


def select_library(libraries: list[LibraryConfig], default_index: int, key: str | None) -> LibraryConfig | None:
    if not key:
        return libraries[default_index]
    return next((library for library in libraries if library.key == key), None)
