from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lazybooks.books import load_books, matches, sort_books
from lazybooks.config import load_libraries, select_library
from lazybooks.files import cached_path, fetch_book, open_file, remote_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the lazybooks manifest and fetch PDFs with rclone.")
    parser.add_argument("--config", help="Path to config.toml. Defaults to LAZYBOOKS_CONFIG or ~/.config/lazybooks/config.toml.")
    parser.add_argument("-l", "--library", help="Library key to search. Defaults to configured default.")
    parser.add_argument("terms", nargs="+", help="Search terms, all must match.")
    parser.add_argument("-n", "--number", type=int, help="Fetch/open result number.")
    parser.add_argument("--no-open", action="store_true", help="Download but do not open.")
    args = parser.parse_args()

    libraries, default_index = load_libraries(Path(args.config).expanduser() if args.config else None)
    library = select_library(libraries, default_index, args.library)
    if library is None:
        print(f"Unknown library: {args.library}", file=sys.stderr)
        print("Available libraries: " + ", ".join(candidate.key for candidate in libraries), file=sys.stderr)
        return 2

    books = sort_books([book for book in load_books(library) if matches(book, args.terms)])
    if not books:
        print("No matches.")
        return 1

    for index, book in enumerate(books, 1):
        print(f"{index:>2}. {book.title} [{book.category}] ({library.name})")
        print(f"    {book.author}")
        print(f"    {book.source}")

    if args.number is None:
        print("\nFetch one with: bookfind <terms> -n <number>")
        return 0

    if args.number < 1 or args.number > len(books):
        print(f"Invalid result number: {args.number}", file=sys.stderr)
        return 2

    book = books[args.number - 1]
    target = cached_path(book, library)
    cached = target.exists()

    if cached:
        print(f"\nOpening cached copy:\n  {target}")
    else:
        src = remote_path(book, library)
        print(f"\nFetching:\n  {src}\n-> {target}")
    target = fetch_book(book, library)

    if not args.no_open:
        open_file(target)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
