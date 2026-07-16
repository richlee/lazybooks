from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lazybooks.config import available_library_keys, matching_libraries, load_libraries
from lazybooks.refresh import RefreshError, refresh_library, report_refresh_error


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh lazybooks index files from rclone remotes.")
    parser.add_argument("--config", help="Path to config.toml. Defaults to LAZYBOOKS_CONFIG or the platform lazybooks config path.")
    parser.add_argument("library", nargs="?", help="Library key to refresh. Defaults to configured default.")
    parser.add_argument("--all", action="store_true", help="Refresh all configured libraries.")
    args = parser.parse_args()

    libraries, default_index = load_libraries(Path(args.config).expanduser() if args.config else None)
    selected = libraries
    if not args.all:
        if args.library:
            selected = matching_libraries(libraries, args.library)
            if not selected:
                print(f"Unknown library: {args.library}", file=sys.stderr)
                print("Available libraries: " + available_library_keys(libraries), file=sys.stderr)
                return 2
            if len(selected) > 1:
                print(f"Ambiguous library: {args.library}", file=sys.stderr)
                print("Use one of: " + ", ".join(f"{library.source_key}.{library.key}" for library in selected), file=sys.stderr)
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
