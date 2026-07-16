from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from lazybooks.books import load_books
from lazybooks.config import DEFAULT_CONFIG, LibraryConfig, ambiguous_library_keys, demo_root, load_libraries


def status_line(ok: bool, label: str, detail: str = "") -> str:
    marker = "OK" if ok else "!!"
    return f"[{marker}] {label}" + (f": {detail}" if detail else "")


def run_text(args: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=15)
    except FileNotFoundError:
        return 127, "", f"{args[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def configured_remote_names(libraries: list[LibraryConfig]) -> set[str]:
    names: set[str] = set()
    for library in libraries:
        if ":" in library.remote:
            remote_name = library.remote.split(":", 1)[0] + ":"
            if remote_name != "demo:":
                names.add(remote_name)
        if ":" in library.index_remote:
            remote_name = library.index_remote.split(":", 1)[0] + ":"
            if remote_name != "demo:":
                names.add(remote_name)
    return names


def can_write_directory(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".lazybooks-check-", dir=path, delete=False) as handle:
            probe = Path(handle.name)
        probe.unlink(missing_ok=True)
        return True, str(path)
    except Exception as exc:
        return False, f"{path} ({exc})"


def check_library(library: LibraryConfig) -> list[tuple[bool, str, str]]:
    checks: list[tuple[bool, str, str]] = []
    checks.append((library.manifest.exists(), f"{library.name} manifest", str(library.manifest)))
    checks.append((library.index_dir.exists(), f"{library.name} index dir", str(library.index_dir)))
    cache_ok, cache_detail = can_write_directory(library.cache)
    checks.append((cache_ok, f"{library.name} cache writable", cache_detail))
    checks.append((bool(library.remote.endswith(":")), f"{library.name} remote", library.remote))
    checks.append((bool(library.local_prefix), f"{library.name} local_prefix", library.local_prefix))
    if library.manifest.exists():
        try:
            books = load_books(library)
            checks.append((True, f"{library.name} books", f"{len(books)} in manifest"))
        except Exception as exc:
            checks.append((False, f"{library.name} books", str(exc)))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Check lazybooks product dependencies and configuration.")
    parser.add_argument("--config", help="Path to config.toml. Defaults to LAZYBOOKS_CONFIG or ~/.config/lazybooks/config.toml.")
    parser.add_argument("--demo", action="store_true", help="Check the packaged demo library.")
    parser.add_argument("--check-remotes", action="store_true", help="Run rclone lsf against configured index remotes.")
    args = parser.parse_args()

    config_path = demo_root() / "config.toml" if args.demo else Path(args.config).expanduser() if args.config else DEFAULT_CONFIG
    config_exists = config_path.exists()
    print(status_line(True, "Python", sys.version.split()[0]))

    try:
        import textual

        print(status_line(True, "Textual", getattr(textual, "__version__", "installed")))
    except Exception as exc:
        print(status_line(False, "Textual", str(exc)))

    rclone_path = shutil.which("rclone")
    print(status_line(bool(rclone_path), "rclone executable", rclone_path or "not found"))
    remotes: set[str] = set()
    if rclone_path:
        code, stdout, stderr = run_text(["rclone", "listremotes"])
        if code == 0:
            remotes = set(stdout.splitlines())
            print(status_line(True, "rclone remotes", ", ".join(sorted(remotes)) or "none configured"))
        else:
            print(status_line(False, "rclone remotes", stderr or stdout or f"exit {code}"))

    if args.config or os.environ.get("LAZYBOOKS_CONFIG"):
        print(status_line(config_exists, "config file", str(config_path)))
    else:
        print(status_line(config_exists, "config file", f"{config_path} (using fallback defaults)" if not config_exists else str(config_path)))

    try:
        libraries, default_index = load_libraries(config_path if config_exists else None)
    except Exception as exc:
        print(status_line(False, "load config", str(exc)))
        return 1

    print(status_line(bool(libraries), "libraries", f"{len(libraries)} configured; default={libraries[default_index].key}"))
    ambiguous = ambiguous_library_keys(libraries)
    if ambiguous:
        detail = "; ".join(f"{key} => {', '.join(values)}" for key, values in sorted(ambiguous.items()))
        print(status_line(False, "ambiguous bare library keys", detail))
    else:
        print(status_line(True, "ambiguous bare library keys", "none"))

    failures = 0
    expected_remotes = configured_remote_names(libraries)
    if expected_remotes and not rclone_path:
        failures += 1
    elif expected_remotes and not remotes:
        failures += 1
    elif rclone_path and remotes:
        missing = sorted(expected_remotes - remotes)
        print(status_line(not missing, "configured rclone remotes", ", ".join(missing) if missing else "all present"))
        failures += 1 if missing else 0

    for library in libraries:
        for ok, label, detail in check_library(library):
            print(status_line(ok, label, detail))
            failures += 0 if ok else 1
        if args.check_remotes and rclone_path:
            code, stdout, stderr = run_text(["rclone", "lsf", library.index_remote])
            ok = code == 0
            detail = "reachable" if ok else stderr or stdout or f"exit {code}"
            print(status_line(ok, f"{library.name} index remote reachable", detail))
            failures += 0 if ok else 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
