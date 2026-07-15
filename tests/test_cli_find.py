from __future__ import annotations

import sys

from lazybooks.cli.find import main


def test_bookfind_lists_sorted_matches(monkeypatch, capsys, library) -> None:
    monkeypatch.setattr(sys, "argv", ["bookfind", "--library", "test", "example"])
    monkeypatch.setattr("lazybooks.cli.find.load_libraries", lambda: ([library], 0))

    assert main() == 0

    output = capsys.readouterr().out
    assert "1. Alpha Architecture" in output
    assert "2. Beta Security" in output
    assert "Fetch one with: bookfind <terms> -n <number>" in output


def test_bookfind_rejects_unknown_library(monkeypatch, capsys, library) -> None:
    monkeypatch.setattr(sys, "argv", ["bookfind", "--library", "missing", "example"])
    monkeypatch.setattr("lazybooks.cli.find.load_libraries", lambda: ([library], 0))

    assert main() == 2

    captured = capsys.readouterr()
    assert "Unknown library: missing" in captured.err
    assert "Available libraries: test" in captured.err
