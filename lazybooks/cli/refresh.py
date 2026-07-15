from __future__ import annotations

import argparse
import sys

from lazybooks.config import load_libraries
from lazybooks.refresh import RefreshError, refresh_library, report_refresh_error


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh lazybooks index files from rclone remotes.")
    parser.add_argument("library", nargs="?", help="Library key to refresh. Defaults to configured default.")
    parser.add_argument("--all", action="store_true", help="Refresh all configured libraries.")
    args = parser.parse_args()

    libraries, default_index = load_libraries()
    selected = libraries
    if not args.all:
        if args.library:
            selected = [library for library in libraries if library.key == args.library]
            if not selected:
                print(f"Unknown library: {args.library}", file=sys.stderr)
                print("Available libraries: " + ", ".join(library.key for library in libraries), file=sys.stderr)
                return 2
        else:
            selected = [libraries[default_index]]

    failures = 0
    for library in selected:
        try:
            refresh_library(library)
            print(f"Refreshed {library.name}:")
            print(f"  {library.index_dir / 'index.html'}")
            print(f"  {library.manifest}")
        except RefreshError as exc:
            report_refresh_error(exc)
            failures += 1
            if not args.all:
                return exc.returncode
        except Exception as exc:
            print(f"Refresh failed for {library.name}: {exc}", file=sys.stderr)
            failures += 1
            if not args.all:
                return 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
