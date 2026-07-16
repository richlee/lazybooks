from __future__ import annotations

import sys
from dataclasses import replace

from lazybooks.cli.find import main


def test_bookfind_lists_sorted_matches(monkeypatch, capsys, library) -> None:
    monkeypatch.setattr(sys, "argv", ["bookfind", "--library", "test", "example"])
    monkeypatch.setattr("lazybooks.cli.find.load_libraries", lambda config_path=None: ([library], 0))

    assert main() == 0

    output = capsys.readouterr().out
    assert "1. Alpha Architecture" in output
    assert "2. Beta Security" in output
    assert "Fetch one with: bookfind <terms> -n <number>" in output


def test_bookfind_rejects_unknown_library(monkeypatch, capsys, library) -> None:
    monkeypatch.setattr(sys, "argv", ["bookfind", "--library", "missing", "example"])
    monkeypatch.setattr("lazybooks.cli.find.load_libraries", lambda config_path=None: ([library], 0))

    assert main() == 2

    captured = capsys.readouterr()
    assert "Unknown library: missing" in captured.err
    assert "Available libraries: default.test" in captured.err


def test_bookfind_accepts_source_qualified_library(monkeypatch, capsys, library) -> None:
    onedrive = replace(library, source_key="onedrive", source_name="OneDrive")
    google = replace(library, source_key="google", source_name="Google Drive")
    monkeypatch.setattr(sys, "argv", ["bookfind", "--library", "google.test", "alpha"])
    monkeypatch.setattr("lazybooks.cli.find.load_libraries", lambda config_path=None: ([onedrive, google], 1))

    assert main() == 0

    output = capsys.readouterr().out
    assert "Alpha Architecture" in output


def test_bookfind_rejects_ambiguous_bare_library(monkeypatch, capsys, library) -> None:
    onedrive = replace(library, source_key="onedrive", source_name="OneDrive")
    google = replace(library, source_key="google", source_name="Google Drive")
    monkeypatch.setattr(sys, "argv", ["bookfind", "--library", "test", "alpha"])
    monkeypatch.setattr("lazybooks.cli.find.load_libraries", lambda config_path=None: ([onedrive, google], 0))

    assert main() == 2

    captured = capsys.readouterr()
    assert "Ambiguous library: test" in captured.err
    assert "onedrive.test, google.test" in captured.err
