from __future__ import annotations

import sys
from dataclasses import replace

from lazybooks.cli import refresh


def test_bookrefresh_accepts_source_qualified_library(monkeypatch, capsys, library) -> None:
    onedrive = replace(library, source_key="onedrive", source_name="OneDrive")
    google = replace(library, source_key="google", source_name="Google Drive")
    refreshed = []

    monkeypatch.setattr(sys, "argv", ["bookrefresh", "google.test"])
    monkeypatch.setattr(refresh, "load_libraries", lambda config_path=None: ([onedrive, google], 0))
    monkeypatch.setattr(refresh, "refresh_library", lambda selected: refreshed.append(selected))

    assert refresh.main() == 0
    assert refreshed == [google]
    assert "Refreshed Test" in capsys.readouterr().out


def test_bookrefresh_rejects_ambiguous_bare_library(monkeypatch, capsys, library) -> None:
    onedrive = replace(library, source_key="onedrive", source_name="OneDrive")
    google = replace(library, source_key="google", source_name="Google Drive")

    monkeypatch.setattr(sys, "argv", ["bookrefresh", "test"])
    monkeypatch.setattr(refresh, "load_libraries", lambda config_path=None: ([onedrive, google], 0))

    assert refresh.main() == 2
    captured = capsys.readouterr()
    assert "Ambiguous library: test" in captured.err
    assert "onedrive.test, google.test" in captured.err
