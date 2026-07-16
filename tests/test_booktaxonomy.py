from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from importlib.machinery import SourceFileLoader
from pathlib import Path


def load_booktaxonomy_module():
    loader = SourceFileLoader("booktaxonomy_script", str(Path("bin/booktaxonomy")))
    spec = importlib.util.spec_from_loader("booktaxonomy_script", loader)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def metadata_book(module, *, title: str, library: str = "tech", tags: str = ""):
    return module.MetadataBook(
        id=1,
        library=library,
        title=title,
        authors="Ada Example",
        tags=tags,
        comments="",
        canonical_path="/tmp/example.pdf",
        db_path=Path("/tmp/metadata.db"),
    )


def test_loads_bundled_taxonomy_profiles() -> None:
    module = load_booktaxonomy_module()

    taxonomy = module.load_taxonomy_config(None)

    assert "tech" in taxonomy.profiles
    assert "personal" in taxonomy.profiles
    assert taxonomy.library_profiles["tech"] == "tech"
    assert taxonomy.profiles["tech"].rules


def test_classify_uses_taxonomy_profile_rules() -> None:
    module = load_booktaxonomy_module()
    taxonomy = module.load_taxonomy_config(None)
    profile = taxonomy.profiles["tech"]
    book = metadata_book(module, title="Kubernetes in Practice")

    proposal = module.classify(book, Counter(), profile)

    assert proposal.category == "cloud-devops-platform"
    assert proposal.confidence == "high"


def test_user_taxonomy_config_overrides_profiles(tmp_path: Path) -> None:
    module = load_booktaxonomy_module()
    config = tmp_path / "taxonomy.toml"
    config.write_text(
        """
[libraries]
tech = "custom"

[profiles.custom]
manual_review_category = "custom-review"

[[profiles.custom.rules]]
category = "custom-category"
keywords = ["special phrase"]
"""
    )

    taxonomy = module.load_taxonomy_config(config)
    profile = taxonomy.profiles["custom"]
    book = metadata_book(module, title="A Special Phrase")

    proposal = module.classify(book, Counter(), profile)

    assert taxonomy.library_profiles["tech"] == "custom"
    assert proposal.category == "custom-category"
