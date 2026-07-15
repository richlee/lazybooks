from __future__ import annotations

import argparse
from dataclasses import dataclass

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from lazybooks.books import Book, build_categories, label_category, load_books, visible_books
from lazybooks.config import LibraryConfig, load_libraries
from lazybooks.files import cached_path, fetch_book, open_file
from lazybooks.refresh import refresh_library
from lazybooks.version import version_info, version_label


HELP_TEXT = "Move: ↑/↓ | Pane: Tab | Search: / | Open: Enter | Details: →/l | Delete cache: d | Library: 1-9 | Refresh: r | About: ? | Quit: q/Esc"


@dataclass
class LibraryState:
    books: list[Book]
    categories: list[str]
    category_index: int = 0
    book_index: int = 0
    query: str = ""


class MessageModal(ModalScreen[None]):
    DEFAULT_CSS = """
    MessageModal {
        align: center middle;
    }

    MessageModal > Vertical {
        width: 68;
        max-width: 90%;
        height: auto;
        max-height: 85%;
        background: $surface;
        border: round $accent;
        padding: 1 2;
    }

    MessageModal .title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    MessageModal .muted {
        color: $text-muted;
    }
    """

    BINDINGS = [Binding("escape,enter,space,?,right,l,q", "close", "Close", show=False)]

    def __init__(self, title: str, lines: list[str]) -> None:
        super().__init__()
        self.title = title
        self.lines = lines

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.title, classes="title")
            for line in self.lines:
                yield Label(line, classes="muted" if line else "")
            yield Label("Any key to close", classes="muted")

    def action_close(self) -> None:
        self.dismiss(None)


class LazyBooksApp(App[None]):
    CSS = """
    Screen {
        background: #20242c;
        color: #d7d7d7;
    }

    Header {
        display: none;
    }

    #root {
        height: 1fr;
    }

    #tabs {
        height: 1;
        color: #a8adb7;
        padding: 0 1;
    }

    #search {
        height: 3;
        border-bottom: solid #585f6b;
    }

    #search_input {
        margin: 0 1;
    }

    #main {
        height: 1fr;
    }

    #categories_panel {
        width: 42;
        min-width: 28;
        border-right: solid #585f6b;
    }

    #books_panel {
        width: 1fr;
    }

    .panel_title {
        height: 1;
        padding: 0 1;
        text-style: bold;
        color: #d7d7d7;
    }

    ListView {
        height: 1fr;
        background: #20242c;
    }

    ListView:focus {
        border: none;
    }

    ListItem {
        height: 1;
        padding: 0 1;
    }

    ListItem.--highlight {
        background: #444444;
        color: #ffaf00;
        text-style: bold;
    }

    .selected_category {
        background: #444444;
        color: #ffaf00;
    }

    .book_author {
        color: #a8adb7;
    }

    #detail {
        height: 4;
        border-top: solid #585f6b;
        color: #a8adb7;
        padding: 0 1;
    }

    #detail_title {
        color: #87d787;
    }

    #status {
        height: 1;
        background: #87d787;
        color: #20242c;
        padding: 0 1;
    }

    Footer {
        display: none;
    }
    """

    BINDINGS = [
        Binding("q,escape", "quit", "Quit", show=False),
        Binding("tab", "toggle_focus", "Pane", show=False),
        Binding("/", "search", "Search", show=False),
        Binding("c", "clear_search", "Clear search", show=False),
        Binding("enter", "open_selected", "Open", show=False),
        Binding("right,l", "details", "Details", show=False),
        Binding("d", "delete_cache", "Delete cache", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("?", "about", "About", show=False),
    ]

    def __init__(self, libraries: list[LibraryConfig], default_index: int) -> None:
        super().__init__()
        self.libraries = libraries
        self.library_index = default_index
        self.state_by_key: dict[str, LibraryState] = {}
        self.focus_pane = "books"
        self.message = HELP_TEXT

    @property
    def library(self) -> LibraryConfig:
        return self.libraries[self.library_index]

    @property
    def state(self) -> LibraryState:
        key = self.library.key
        if key not in self.state_by_key:
            self.state_by_key[key] = self.load_state(self.library)
        return self.state_by_key[key]

    def load_state(self, library: LibraryConfig) -> LibraryState:
        try:
            books = load_books(library)
            return LibraryState(books=books, categories=build_categories(books))
        except Exception as exc:
            self.message = f"Could not load {library.name}: {exc}"
            return LibraryState(books=[], categories=["All"])

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="root"):
            yield Static(id="tabs")
            with Vertical(id="search"):
                yield Input(placeholder="Search", id="search_input")
            with Horizontal(id="main"):
                with Vertical(id="categories_panel"):
                    yield Static(" Categories", classes="panel_title")
                    yield ListView(id="categories")
                with Vertical(id="books_panel"):
                    yield Static(" Books", classes="panel_title")
                    yield ListView(id="books")
            with Vertical(id="detail"):
                yield Static(id="detail_title")
                yield Static(id="detail_meta")
                yield Static(id="detail_path")
            yield Static(HELP_TEXT, id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search_input", Input).display = False
        self.refresh_all_views()
        self.query_one("#books", ListView).focus()

    def visible(self) -> list[Book]:
        category = self.state.categories[self.state.category_index] if self.state.categories else "All"
        return visible_books(self.state.books, category, self.state.query)

    def refresh_all_views(self) -> None:
        self.update_tabs()
        self.update_search()
        self.update_categories()
        self.update_books()
        self.update_detail()
        self.update_status()

    def update_tabs(self) -> None:
        labels = []
        for index, library in enumerate(self.libraries[:9], start=1):
            label = f"[{index}] {library.name}"
            labels.append(f"[reverse]{label}[/]" if index - 1 == self.library_index else label)
        self.query_one("#tabs", Static).update("  ".join(labels))

    def update_search(self) -> None:
        search_input = self.query_one("#search_input", Input)
        search_input.value = self.state.query

    def update_categories(self) -> None:
        view = self.query_one("#categories", ListView)
        view.clear()
        counts = {category: 0 for category in self.state.categories}
        counts["All"] = len(self.state.books)
        for book in self.state.books:
            counts[book.category] = counts.get(book.category, 0) + 1
        for index, category in enumerate(self.state.categories):
            label = label_category(category) if category != "All" else "All"
            item = ListItem(Label(f"{label} ({counts.get(category, 0)})"))
            if index == self.state.category_index:
                item.add_class("selected_category")
            view.append(item)
        if self.state.categories:
            view.index = self.state.category_index

    def update_books(self) -> None:
        view = self.query_one("#books", ListView)
        view.clear()
        books = self.visible()
        self.state.book_index = min(max(0, self.state.book_index), max(0, len(books) - 1))
        for book in books:
            author = f" - {book.author}" if book.author and book.author != "Unknown" else ""
            view.append(ListItem(Label(f"{book.title}[dim]{author}[/]")))
        if books:
            view.index = self.state.book_index

    def update_detail(self) -> None:
        books = self.visible()
        if not books:
            self.query_one("#detail_title", Static).update("")
            self.query_one("#detail_meta", Static).update("No book selected")
            self.query_one("#detail_path", Static).update("")
            return
        book = books[self.state.book_index]
        cache_state = "cached" if cached_path(book, self.library).exists() else "not cached"
        self.query_one("#detail_title", Static).update(f"{book.title}")
        self.query_one("#detail_meta", Static).update(
            f"{book.author} | {label_category(book.category)} | Cache: {cache_state} | Source: {book.source}"
        )
        self.query_one("#detail_path", Static).update(book.canonical_path)

    def update_status(self) -> None:
        self.query_one("#status", Static).update(self.message or HELP_TEXT)

    def set_message(self, message: str) -> None:
        self.message = message
        self.update_status()
        self.set_timer(3.0, self.clear_message)

    def clear_message(self) -> None:
        self.message = HELP_TEXT
        self.update_status()

    def switch_library(self, index: int) -> None:
        if index < 0 or index >= len(self.libraries):
            return
        self.library_index = index
        self.focus_pane = "books"
        self.refresh_all_views()
        self.query_one("#books", ListView).focus()
        self.set_message(f"Switched to {self.library.name}")

    def on_key(self, event) -> None:
        if event.key and len(event.key) == 1 and event.key.isdigit() and event.key != "0":
            self.switch_library(int(event.key) - 1)
            event.stop()

    @on(ListView.Highlighted, "#categories")
    def category_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.has_focus and event.list_view.index is not None:
            self.state.category_index = event.list_view.index
            self.state.book_index = 0
            self.update_categories()
            self.update_books()
            self.update_detail()

    @on(ListView.Highlighted, "#books")
    def book_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.has_focus and event.list_view.index is not None:
            self.state.book_index = event.list_view.index
            self.update_detail()

    @on(Input.Submitted, "#search_input")
    def search_submitted(self, event: Input.Submitted) -> None:
        self.state.query = event.value.strip()
        self.state.book_index = 0
        self.query_one("#search_input", Input).display = False
        self.focus_pane = "books"
        self.refresh_all_views()
        self.query_one("#books", ListView).focus()
        self.set_message("Search updated" if self.state.query else "Search cleared")

    def action_toggle_focus(self) -> None:
        if self.focus_pane == "books":
            self.focus_pane = "categories"
            self.query_one("#categories", ListView).focus()
        else:
            self.focus_pane = "books"
            self.query_one("#books", ListView).focus()

    def action_search(self) -> None:
        search = self.query_one("#search_input", Input)
        search.display = True
        search.value = self.state.query
        search.focus()

    def action_clear_search(self) -> None:
        self.state.query = ""
        self.state.book_index = 0
        self.query_one("#search_input", Input).display = False
        self.refresh_all_views()
        self.query_one("#books", ListView).focus()
        self.set_message("Search cleared")

    def selected_book(self) -> Book | None:
        books = self.visible()
        if not books:
            return None
        return books[min(self.state.book_index, len(books) - 1)]

    @work(thread=True)
    def action_open_selected(self) -> None:
        book = self.selected_book()
        if book is None:
            self.call_from_thread(self.set_message, "No book selected")
            return
        self.call_from_thread(self.set_message, f"Fetching {book.title}...")
        try:
            target = fetch_book(book, self.library)
            open_file(target)
            self.call_from_thread(self.set_message, f"Opened {target.name}")
            self.call_from_thread(self.update_detail)
        except Exception as exc:
            self.call_from_thread(self.set_message, f"Fetch failed: {exc}")

    def action_delete_cache(self) -> None:
        book = self.selected_book()
        if book is None:
            self.set_message("No book selected")
            return
        path = cached_path(book, self.library)
        if not path.exists():
            self.set_message("No cached copy to delete")
            return
        try:
            path.unlink()
            self.update_detail()
            self.set_message(f"Deleted cached copy: {path.name}")
        except Exception as exc:
            self.set_message(f"Delete failed: {exc}")

    @work(thread=True)
    def action_refresh(self) -> None:
        self.call_from_thread(self.set_message, f"Refreshing {self.library.name}...")
        try:
            refresh_library(self.library)
            self.state_by_key[self.library.key] = self.load_state(self.library)
            self.call_from_thread(self.refresh_all_views)
            self.call_from_thread(self.set_message, "Index refreshed")
        except Exception as exc:
            self.call_from_thread(self.set_message, f"Refresh failed: {exc}")

    def action_details(self) -> None:
        book = self.selected_book()
        if book is None:
            self.set_message("No book selected")
            return
        cache_state = "cached" if cached_path(book, self.library).exists() else "not cached"
        lines = [
            f"Title: {book.title}",
            f"Author: {book.author}",
            f"Category: {label_category(book.category)}",
            f"Source: {book.source}",
            f"Cache: {cache_state}",
            f"Local: {cached_path(book, self.library)}",
            f"Path: {book.canonical_path}",
        ]
        self.push_screen(MessageModal("Book details", lines), lambda _: self.set_message("Details closed"))

    def action_about(self) -> None:
        version, commit, commit_date = version_info()
        lines = [
            "Lazy terminal access to cloud-hosted book libraries.",
            "",
            f"Version: {version}",
            f"Commit: {commit}",
            f"Commit date: {commit_date}",
            "License: MIT",
            "",
            "Created by Rich Lee, LeeSoft",
            "Contact: Rich Lee <richalee@pm.me>",
            "Built with OpenAI Codex",
            "",
            "Tech stack: Python, Textual, rclone, JSON manifests, Calibre SQLite metadata, OneDrive, optional fzf.",
        ]
        self.push_screen(MessageModal("lazybooks", lines), lambda _: self.set_message("About closed"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Browse lazybooks libraries.")
    parser.add_argument("--version", "-V", action="store_true", help="Show version and exit.")
    args = parser.parse_args()
    if args.version:
        print(version_label())
        return 0

    libraries, default_index = load_libraries()
    LazyBooksApp(libraries, default_index).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
