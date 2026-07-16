from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from subprocess import run

from lazybooks.cli import index as bookindex_module
from lazybooks.config import LibraryConfig


def load_bookindex_module():
    return bookindex_module


def test_bookindex_writes_remote_path_for_matching_prefix(tmp_path: Path) -> None:
    library = tmp_path / "library"
    section = library / "architecture"
    section.mkdir(parents=True)
    pdf = section / "Secure by Design - Dan Bergh Johnsson.pdf"
    pdf.write_text("placeholder")
    index_dir = tmp_path / "index"

    result = run(
        [
            sys.executable,
            "-m",
            "lazybooks.cli.index",
            "--root",
            str(library),
            "--index-dir",
            str(index_dir),
            "--title",
            "Test Books",
            "--library-name",
            "Test",
            "--category-depth",
            "1",
            "--local-prefix",
            str(library) + os.sep,
            "--remote",
            "google-drive:Library/test/",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads((index_dir / "manifest.json").read_text())
    assert json.loads(result.stdout)["books"] == 1
    assert manifest["books"][0]["remote_path"] == "google-drive:Library/test/architecture/Secure by Design - Dan Bergh Johnsson.pdf"


def test_bookindex_all_uses_configured_library_roots(tmp_path: Path) -> None:
    library = tmp_path / "library"
    section = library / "architecture"
    section.mkdir(parents=True)
    pdf = section / "Reliable APIs - Ada Example.pdf"
    pdf.write_text("placeholder")
    index_dir = tmp_path / "index"
    config = tmp_path / "config.toml"
    library_config_path = library.as_posix()
    index_config_path = index_dir.as_posix()
    config.write_text(
        f"""
default_source = "google"
default_library = "reference"

[sources.google]
name = "Google Drive"
remote = "google-drive:"
local_prefix = "{library_config_path}/"

[sources.google.libraries.reference]
name = "Reference"
root = "{library_config_path}"
index_dir = "{index_config_path}"
index_remote = "google-drive:Library/book-indexes/reference"
title = "Reference Books"
library_name = "Reference"
category_depth = 1
"""
    )

    result = run(
        [sys.executable, "-m", "lazybooks.cli.index", "--config", str(config), "--all"],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    manifest = json.loads((index_dir / "manifest.json").read_text())
    assert output["indexed"][0]["library"] == "reference"
    assert output["indexed"][0]["books"] == 1
    assert manifest["books"][0]["remote_path"] == "google-drive:architecture/Reliable APIs - Ada Example.pdf"


def test_bookindex_library_rejects_ambiguous_bare_key(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    for name in ("one", "two"):
        library = tmp_path / name / "library"
        library.mkdir(parents=True)
        (library / f"{name.title()} Book - Ada Example.pdf").write_text("placeholder")
    config.write_text(
        f"""
default_source = "one"
default_library = "reference"

[sources.one]
name = "One"
remote = "one:"
local_prefix = "{(tmp_path / "one" / "library").as_posix()}/"

[sources.one.libraries.reference]
name = "Reference"
root = "{(tmp_path / "one" / "library").as_posix()}"
index_dir = "{(tmp_path / "one-index").as_posix()}"
index_remote = "one:index/reference"

[sources.two]
name = "Two"
remote = "two:"
local_prefix = "{(tmp_path / "two" / "library").as_posix()}/"

[sources.two.libraries.reference]
name = "Reference"
root = "{(tmp_path / "two" / "library").as_posix()}"
index_dir = "{(tmp_path / "two-index").as_posix()}"
index_remote = "two:index/reference"
"""
    )

    result = run(
        [sys.executable, "-m", "lazybooks.cli.index", "--config", str(config), "--library", "reference"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Ambiguous library: reference" in result.stderr
    assert "one.reference" in result.stderr
    assert "two.reference" in result.stderr


def test_bookindex_library_accepts_source_qualified_key(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir(parents=True)
    (library / "Qualified Book - Ada Example.pdf").write_text("placeholder")
    index_dir = tmp_path / "index"
    config = tmp_path / "config.toml"
    config.write_text(
        f"""
[sources.google]
name = "Google Drive"
remote = "google-drive:"
local_prefix = "{library.as_posix()}/"

[sources.google.libraries.reference]
name = "Reference"
root = "{library.as_posix()}"
index_dir = "{index_dir.as_posix()}"
index_remote = "google-drive:index/reference"
"""
    )

    result = run(
        [sys.executable, "-m", "lazybooks.cli.index", "--config", str(config), "--library", "google.reference"],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert output["indexed"][0]["source"] == "google"
    assert output["indexed"][0]["library"] == "reference"
    assert output["indexed"][0]["books"] == 1


def test_publish_configured_library_uses_filtered_rclone_copy(monkeypatch, tmp_path: Path) -> None:
    module = load_bookindex_module()
    calls = []

    class Result:
        returncode = 0
        stderr = ""

    def fake_run(command, capture_output, text):
        calls.append((command, capture_output, text))
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    library = LibraryConfig(
        key="reference",
        name="Reference",
        manifest=tmp_path / "index" / "manifest.json",
        index_dir=tmp_path / "index",
        index_remote="google-drive:Library/book-indexes/reference",
        cache=tmp_path / "cache",
        remote="google-drive:",
        local_prefix="/library/",
        source_key="google",
        source_name="Google Drive",
    )

    module.publish_configured_library(library)

    assert calls == [
        (
            [
                "rclone",
                "copy",
                str(tmp_path / "index"),
                "google-drive:Library/book-indexes/reference",
                "--filter",
                "+ index.html",
                "--filter",
                "+ manifest.json",
                "--filter",
                "- *",
            ],
            True,
            True,
        )
    ]
