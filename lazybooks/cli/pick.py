from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from lazybooks.books import load_books
from lazybooks.config import available_library_keys, load_libraries, matching_libraries, select_library
from lazybooks.files import cached_path, fetch_book, open_file


def choose_library(library_key: str | None, config: str | None):
    libraries, default_index = load_libraries(Path(config).expanduser() if config else None)
    if library_key:
        matches = matching_libraries(libraries, library_key)
        if not matches:
            print(f"Unknown library: {library_key}", file=sys.stderr)
            print("Available libraries: " + available_library_keys(libraries), file=sys.stderr)
            raise SystemExit(2)
        if len(matches) > 1:
            print(f"Ambiguous library: {library_key}", file=sys.stderr)
            print("Use one of: " + ", ".join(f"{library.source_key}.{library.key}" for library in matches), file=sys.stderr)
            raise SystemExit(2)
    library = select_library(libraries, default_index, library_key)
    if library is None:
        print(f"Unknown library: {library_key}", file=sys.stderr)
        raise SystemExit(2)
    return library


def row(index: int, book) -> str:
    return "\t".join(
        [
            str(index),
            book.category,
            book.title,
            book.author,
            book.source,
            book.canonical_path,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Pick a lazybooks PDF with fzf, then fetch and open it.")
    parser.add_argument("library", nargs="?", help="Library key, e.g. tech or onedrive.tech. Defaults to configured default.")
    parser.add_argument("--config", help="Path to config.toml. Defaults to LAZYBOOKS_CONFIG or ~/.config/lazybooks/config.toml.")
    parser.add_argument("--no-open", action="store_true", help="Fetch the selected PDF without opening it.")
    args = parser.parse_args()

    if shutil.which("fzf") is None:
        print("fzf is not installed.", file=sys.stderr)
        return 1

    library = choose_library(args.library, args.config)
    if not library.manifest.exists():
        print(f"Missing manifest: {library.manifest}", file=sys.stderr)
        print("Run bookrefresh first.", file=sys.stderr)
        return 1

    books = load_books(library)
    lines = "\n".join(row(index, book) for index, book in enumerate(books))
    command = [
        "fzf",
        "--delimiter=\t",
        "--with-nth=2,3,4",
        f"--prompt={library.name}> ",
        "--header=Enter: fetch/open | type to filter",
        "--preview=printf 'Category: {2}\nTitle: {3}\nAuthor: {4}\nSource: {5}\n\nPath:\n{6}\n'",
        "--preview-window=down,8",
    ]
    result = subprocess.run(command, input=lines, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return 0

    index = int(result.stdout.split("\t", 1)[0])
    book = books[index]
    target = cached_path(book, library)
    if not target.exists():
        target = fetch_book(book, library)
    if not args.no_open:
        open_file(target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
