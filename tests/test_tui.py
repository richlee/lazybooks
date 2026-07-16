from __future__ import annotations

import asyncio
from pathlib import Path

import lazybooks.tui.textual_app as textual_app
from lazybooks.config import LibraryConfig, SourceConfig
from lazybooks.tui.textual_app import LazyBooksApp, MessageModal, shortcut_row
from textual.widgets import Input, ListView, Static


def run_async(coro):
    return asyncio.run(coro)


def reverse_text(rendered) -> list[str]:
    if not hasattr(rendered, "spans"):
        return []
    return [rendered.plain[span.start : span.end] for span in rendered.spans if "reverse" in str(span.style)]


def test_search_is_not_in_tab_sequence(library) -> None:
    async def scenario() -> None:
        app = LazyBooksApp([library], 0)
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            search = app.query_one("#search_input", Input)
            categories = app.query_one("#categories", ListView)
            books = app.query_one("#books", ListView)

            assert books.has_focus
            assert search.can_focus is False

            await pilot.press("tab")
            await pilot.pause(0.1)
            assert categories.has_focus
            assert not search.has_focus

            await pilot.press("tab")
            await pilot.pause(0.1)
            assert books.has_focus
            assert not search.has_focus

            await pilot.press("/", "a", "l", "p", "h", "a", "enter")
            await pilot.pause(0.2)
            assert app.state.query == "alpha"
            assert search.display is True
            assert search.can_focus is False
            assert books.has_focus

    run_async(scenario())


def test_source_switch_changes_available_libraries(tmp_path: Path, library) -> None:
    google_manifest = tmp_path / "google-manifest.json"
    google_manifest.write_text(
        """
{"books": [
  {
    "title": "Gamma Google",
    "author": "Gina Example",
    "category": "personal-growth",
    "source": "Google Drive",
    "canonical_path": "/google/Gamma Google.pdf"
  }
]}
"""
    )
    google_library = LibraryConfig(
        key="personal",
        name="Personal",
        manifest=google_manifest,
        index_dir=tmp_path / "google-index",
        index_remote="google:Library/book-indexes/personal",
        cache=tmp_path / "google-cache",
        remote="google:",
        local_prefix="/google/",
        source_key="google",
        source_name="Google Drive",
    )
    onedrive_library = LibraryConfig(
        key=library.key,
        name=library.name,
        manifest=library.manifest,
        index_dir=library.index_dir,
        index_remote=library.index_remote,
        cache=library.cache,
        remote=library.remote,
        local_prefix=library.local_prefix,
        source_key="onedrive",
        source_name="OneDrive",
    )

    async def scenario() -> None:
        app = LazyBooksApp(
            [
                SourceConfig("onedrive", "OneDrive", [onedrive_library]),
                SourceConfig("google", "Google Drive", [google_library]),
            ],
            0,
            0,
        )
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            assert app.source.key == "onedrive"
            assert app.library.key == "test"
            assert app.visible()[0].title == "Alpha Architecture"

            await pilot.press("b")
            await pilot.pause(0.2)
            assert app.source.key == "google"
            assert app.library.key == "personal"
            assert app.visible()[0].title == "Gamma Google"

    run_async(scenario())


def test_source_row_shows_shortcut_brackets(library) -> None:
    async def scenario() -> None:
        app = LazyBooksApp(
            [
                SourceConfig("onedrive", "OneDrive", [library]),
                SourceConfig("google", "Google Drive", [library]),
                SourceConfig("dropbox", "Dropbox", [library]),
            ],
            0,
            0,
        )
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            sources = app.query_one("#sources", Static)
            rendered = sources.render()
            text = rendered.plain if hasattr(rendered, "plain") else str(rendered)
            assert "[a] OneDrive" in text
            assert "[b] Google Drive" in text
            assert "[c] Dropbox" in text

    run_async(scenario())


def test_shortcut_row_moves_reverse_highlight() -> None:
    row = shortcut_row("Sources", ["[a] OneDrive", "[b] Google Drive"], 0)
    assert row.plain == "Sources: [a] OneDrive  [b] Google Drive"
    assert reverse_text(row) == ["[a] OneDrive"]

    row = shortcut_row("Sources", ["[a] OneDrive", "[b] Google Drive"], 1)
    assert reverse_text(row) == ["[b] Google Drive"]


def test_category_change_selects_first_visible_book(library) -> None:
    async def scenario() -> None:
        app = LazyBooksApp([library], 0)
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            categories = app.query_one("#categories", ListView)
            books = app.query_one("#books", ListView)

            await pilot.press("tab")
            await pilot.pause(0.1)
            assert categories.has_focus

            await pilot.press("down")
            await pilot.pause(0.2)
            assert categories.has_focus
            assert app.state.book_index == 0
            assert books.index == 0
            assert books.children[0].has_class("selected_book")

            await pilot.press("enter")
            await pilot.pause(0.2)
            assert books.has_focus
            assert app.state.book_index == 0
            assert books.children[0].has_class("selected_book")

            await pilot.press("tab")
            await pilot.pause(0.1)
            assert categories.has_focus
            await pilot.press("up")
            await pilot.pause(0.2)
            assert app.state.category_index == 0
            await pilot.press("enter")
            await pilot.pause(0.2)
            assert books.has_focus

            await pilot.press("down")
            await pilot.pause(0.2)
            assert app.state.book_index == 1
            assert not books.children[0].has_class("selected_book")
            assert books.children[1].has_class("selected_book")

            await pilot.press("tab")
            await pilot.pause(0.1)
            assert categories.has_focus
            await pilot.press("tab")
            await pilot.pause(0.1)
            assert books.has_focus
            assert books.children[1].has_class("selected_book")

    run_async(scenario())


def test_details_and_delete_are_books_pane_only(monkeypatch, library, tmp_path: Path) -> None:
    async def scenario() -> None:
        cached = tmp_path / "cached.pdf"
        cached.write_text("cached")
        monkeypatch.setattr(textual_app, "cached_path", lambda book, config: cached)

        app = LazyBooksApp([library], 0)
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            books = app.query_one("#books", ListView)
            categories = app.query_one("#categories", ListView)

            await pilot.press("tab")
            await pilot.pause(0.1)
            assert categories.has_focus

            await pilot.press("right")
            await pilot.pause(0.2)
            assert not isinstance(app.screen, MessageModal)

            await pilot.press("d")
            await pilot.pause(0.1)
            assert cached.exists()
            assert categories.has_focus

            await pilot.press("tab")
            await pilot.pause(0.1)
            assert books.has_focus

            await pilot.press("right")
            await pilot.pause(0.2)
            assert isinstance(app.screen, MessageModal)
            await pilot.press("x")
            await pilot.pause(0.1)

            await pilot.press("d")
            await pilot.pause(0.2)
            assert books.has_focus
            assert not cached.exists()

    run_async(scenario())


def test_open_uses_cache_and_refreshes_cache_marker(monkeypatch, library, tmp_path: Path) -> None:
    async def scenario() -> None:
        cached = tmp_path / "cached.pdf"
        calls: list[tuple[str, str]] = []

        def fake_fetch(book, config):
            cached.write_text("cached")
            calls.append(("fetch", book.title))
            return cached

        def fake_open(path):
            calls.append(("open", Path(path).name))

        monkeypatch.setattr(textual_app, "cached_path", lambda book, config: cached)
        monkeypatch.setattr(textual_app, "fetch_book", fake_fetch)
        monkeypatch.setattr(textual_app, "open_file", fake_open)

        app = LazyBooksApp([library], 0)
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            assert app.cache_marker(app.selected_book()) == " "

            await pilot.press("enter")
            await pilot.pause(0.5)
            assert calls == [("fetch", "Alpha Architecture"), ("open", "cached.pdf")]
            assert app.cache_marker(app.selected_book()) == "[green]C[/]"

            await pilot.press("enter")
            await pilot.pause(0.5)
            assert calls == [
                ("fetch", "Alpha Architecture"),
                ("open", "cached.pdf"),
                ("open", "cached.pdf"),
            ]

    run_async(scenario())
