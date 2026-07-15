from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import LibraryConfig


@dataclass(frozen=True)
class Book:
    title: str
    author: str
    category: str
    source: str
    canonical_path: str
    remote_path: str = ""
    size: int | None = None
    created_at: str = ""


def book_from_manifest(item: dict) -> Book:
    size = item.get("size")
    return Book(
        title=item.get("title", ""),
        author=item.get("author", "Unknown"),
        category=item.get("category", ""),
        source=item.get("source", ""),
        canonical_path=item.get("canonical_path", ""),
        remote_path=item.get("remote_path", ""),
        size=size if isinstance(size, int) else None,
        created_at=item.get("created_at", ""),
    )


def load_books(library: LibraryConfig) -> list[Book]:
    data = json.loads(library.manifest.read_text())
    return [book_from_manifest(item) for item in data["books"]]


def label_category(category: str) -> str:
    if category == "TOGAF":
        return "TOGAF Reference"
    return category.replace("-", " ").title()


def safe_name(book: Book | dict) -> str:
    title = book["title"] if isinstance(book, dict) else book.title
    name = re.sub(r"[/:]+", " - ", title)
    name = re.sub(r"\s+", " ", name).strip()
    return f"{name}.pdf"


def matches(book: Book, terms: list[str]) -> bool:
    haystack = " ".join([book.title, book.author, book.category, book.source]).casefold()
    return all(term.casefold() in haystack for term in terms)


def visible_books(books: list[Book], category: str, query: str) -> list[Book]:
    terms = [term.casefold() for term in query.split() if term.strip()]
    result: list[Book] = []
    for book in books:
        if category != "All" and book.category != category:
            continue
        haystack = " ".join([book.title, book.author, book.category, book.source]).casefold()
        if all(term in haystack for term in terms):
            result.append(book)
    return sorted(result, key=lambda item: item.title.casefold())


def build_categories(books: list[Book]) -> list[str]:
    cats = sorted({book.category for book in books}, key=lambda value: label_category(value).casefold())
    return ["All"] + cats


def manifest_path(path: str | Path) -> Path:
    return Path(path).expanduser()

