from __future__ import annotations

from lazybooks.books import build_categories, label_category, load_books, matches, safe_name, visible_books


def test_load_books_and_visible_books_are_sorted(library) -> None:
    books = load_books(library)

    assert [book.title for book in visible_books(books, "All", "")] == [
        "Alpha Architecture",
        "Beta Security",
        "Zeta Operations",
    ]


def test_visible_books_filters_by_category_and_query(library) -> None:
    books = load_books(library)

    assert [book.title for book in visible_books(books, "software-architecture-design", "ada")] == [
        "Alpha Architecture"
    ]
    assert visible_books(books, "security-reliability", "architecture") == []


def test_matches_uses_title_author_category_and_source(library) -> None:
    books = load_books(library)
    book = next(book for book in books if book.title == "Beta Security")

    assert matches(book, ["ben", "security"])
    assert matches(book, ["test", "calibre"])
    assert not matches(book, ["operations"])


def test_categories_and_labels(library) -> None:
    books = load_books(library)

    assert build_categories(books) == [
        "All",
        "operations-platform",
        "security-reliability",
        "software-architecture-design",
    ]
    assert label_category("TOGAF") == "TOGAF Reference"
    assert label_category("software-architecture-design") == "Software Architecture Design"


def test_safe_name_sanitises_path_separators() -> None:
    assert safe_name({"title": "A/B: C"}) == "A - B - C.pdf"
