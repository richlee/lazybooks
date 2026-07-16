from __future__ import annotations

from pathlib import Path

import lazybooks.files as files
from lazybooks.books import load_books


def test_remote_path_prefers_manifest_remote_path(library) -> None:
    book = next(book for book in load_books(library) if book.title == "Zeta Operations")

    assert files.remote_path(book, library) == "remote:Library/Zeta Operations.pdf"


def test_remote_path_rewrites_local_prefix(library) -> None:
    book = next(book for book in load_books(library) if book.title == "Alpha Architecture")

    assert files.remote_path(book, library) == "remote:Library/Alpha Architecture.pdf"


def test_fetch_book_uses_cache_without_rclone(monkeypatch, library) -> None:
    book = next(book for book in load_books(library) if book.title == "Alpha Architecture")
    target = files.cached_path(book, library)
    target.parent.mkdir(parents=True)
    target.write_text("cached")

    def fail_run(*args, **kwargs):
        raise AssertionError("rclone should not run for cached files")

    monkeypatch.setattr(files.subprocess, "run", fail_run)

    assert files.fetch_book(book, library) == target


def test_fetch_book_downloads_to_cache(monkeypatch, library) -> None:
    book = next(book for book in load_books(library) if book.title == "Alpha Architecture")
    calls = []

    def fake_run(args, check):
        calls.append((args, check))

    monkeypatch.setattr(files.subprocess, "run", fake_run)

    target = files.fetch_book(book, library)

    assert target == library.cache / library.source_key / library.key / "Alpha Architecture.pdf"
    assert calls == [
        (
            [
                "rclone",
                "copyto",
                "remote:Library/Alpha Architecture.pdf",
                str(Path(library.cache) / library.source_key / library.key / "Alpha Architecture.pdf"),
            ],
            True,
        )
    ]


def test_cached_path_is_scoped_by_source_and_library(library) -> None:
    book = next(book for book in load_books(library) if book.title == "Alpha Architecture")

    assert files.cached_path(book, library).relative_to(library.cache).parts[:2] == (
        library.source_key,
        library.key,
    )
