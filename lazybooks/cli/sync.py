from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def command_path(name: str) -> str:
    sibling = Path(sys.argv[0]).resolve().parent / name
    return str(sibling) if sibling.exists() else name


def run_step(command: list[str]) -> int:
    print("+ " + " ".join(command), flush=True)
    result = subprocess.run(command)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build, publish, and refresh configured lazybooks indexes.")
    parser.add_argument("--config", help="Path to config.toml. Defaults to LAZYBOOKS_CONFIG or the platform lazybooks config path.")
    parser.add_argument("--skip-refresh", action="store_true", help="Only build and publish indexes.")
    parser.add_argument("--skip-index", action="store_true", help="Only refresh already-published indexes.")
    args = parser.parse_args(argv)

    config_args = ["--config", str(Path(args.config).expanduser())] if args.config else []
    if not args.skip_index:
        code = run_step([command_path("bookindex"), *config_args, "--all", "--publish"])
        if code:
            return code
    if not args.skip_refresh:
        code = run_step([command_path("bookrefresh"), *config_args, "--all"])
        if code:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
