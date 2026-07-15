from __future__ import annotations

import json
from pathlib import Path

import pytest

from lazybooks.config import LibraryConfig


@pytest.fixture
def manifest_items() -> list[dict]:
    return [
        {
            "title": "Zeta Operations",
            "author": "Zed Author",
            "category": "operations-platform",
            "source": "Test Calibre",
            "canonical_path": "/cloud/Library/Zeta Operations.pdf",
            "remote_path": "remote:Library/Zeta Operations.pdf",
            "size": 123,
        },
        {
            "title": "Alpha Architecture",
            "author": "Ada Example",
            "category": "software-architecture-design",
            "source": "Test Calibre",
            "canonical_path": "/cloud/Library/Alpha Architecture.pdf",
        },
        {
            "title": "Beta Security",
            "author": "Ben Example",
            "category": "security-reliability",
            "source": "Test Calibre",
            "canonical_path": "/cloud/Library/Beta Security.pdf",
        },
    ]


@pytest.fixture
def library(tmp_path: Path, manifest_items: list[dict]) -> LibraryConfig:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"books": manifest_items}))
    return LibraryConfig(
        key="test",
        name="Test",
        manifest=manifest,
        index_dir=tmp_path / "index",
        index_remote="remote:Library/book-indexes/test",
        cache=tmp_path / "cache",
        remote="remote:",
        local_prefix="/cloud/",
    )
