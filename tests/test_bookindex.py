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
