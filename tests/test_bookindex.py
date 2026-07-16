from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from subprocess import run


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
            "bin/bookindex",
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
        [sys.executable, "bin/bookindex", "--config", str(config), "--all"],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    manifest = json.loads((index_dir / "manifest.json").read_text())
    assert output["indexed"][0]["library"] == "reference"
    assert output["indexed"][0]["books"] == 1
    assert manifest["books"][0]["remote_path"] == "google-drive:architecture/Reliable APIs - Ada Example.pdf"
