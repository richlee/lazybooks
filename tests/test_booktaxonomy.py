from __future__ import annotations

from collections import Counter
from pathlib import Path

from lazybooks.cli import taxonomy as booktaxonomy_module


def load_booktaxonomy_module():
    return booktaxonomy_module


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
