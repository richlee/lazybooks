from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from lazybooks.cli import doctor
from lazybooks.config import LibraryConfig


def test_doctor_reports_missing_rclone_without_failing_for_demo(monkeypatch, capsys, tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"books": []}')
    library = LibraryConfig(
        key="demo",
        name="Demo",
        manifest=manifest,
        index_dir=tmp_path,
        index_remote="demo:index",
        cache=tmp_path / "cache",
        remote="demo:",
        local_prefix="/demo/",
    )

    monkeypatch.setattr(sys, "argv", ["lazybooks-doctor", "--config", str(tmp_path / "config.toml")])
    monkeypatch.setattr(doctor, "load_libraries", lambda config_path=None: ([library], 0))
    monkeypatch.setattr(doctor.shutil, "which", lambda command: None)

    assert doctor.main() == 0

    output = capsys.readouterr().out
    assert "[!!] rclone executable: not found" in output
    assert "[OK] Demo books: 0 in manifest" in output


def test_doctor_flags_missing_manifest(monkeypatch, tmp_path: Path) -> None:
    library = LibraryConfig(
        key="demo",
        name="Demo",
        manifest=tmp_path / "missing.json",
        index_dir=tmp_path,
        index_remote="demo:index",
        cache=tmp_path / "cache",
        remote="demo:",
        local_prefix="/demo/",
    )

    monkeypatch.setattr(sys, "argv", ["lazybooks-doctor"])
    monkeypatch.setattr(doctor, "load_libraries", lambda config_path=None: ([library], 0))
    monkeypatch.setattr(doctor.shutil, "which", lambda command: None)

    assert doctor.main() == 1


def test_doctor_requires_rclone_for_real_remote(monkeypatch, tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"books": []}')
    library = LibraryConfig(
        key="real",
        name="Real",
        manifest=manifest,
        index_dir=tmp_path,
        index_remote="personal-onedrive:index",
        cache=tmp_path / "cache",
        remote="personal-onedrive:",
        local_prefix="/library/",
    )

    monkeypatch.setattr(sys, "argv", ["lazybooks-doctor"])
    monkeypatch.setattr(doctor, "load_libraries", lambda config_path=None: ([library], 0))
    monkeypatch.setattr(doctor.shutil, "which", lambda command: None)

    assert doctor.main() == 1


def test_doctor_warns_for_ambiguous_bare_library_keys(monkeypatch, capsys, tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"books": []}')
    library = LibraryConfig(
        key="assurance",
        name="Assurance",
        manifest=manifest,
        index_dir=tmp_path,
        index_remote="demo:index",
        cache=tmp_path / "cache",
        remote="demo:",
        local_prefix="/demo/",
    )
    onedrive = replace(library, source_key="onedrive", source_name="OneDrive")
    google = replace(library, source_key="google", source_name="Google Drive")

    monkeypatch.setattr(sys, "argv", ["lazybooks-doctor"])
    monkeypatch.setattr(doctor, "load_libraries", lambda config_path=None: ([onedrive, google], 0))
    monkeypatch.setattr(doctor.shutil, "which", lambda command: None)

    assert doctor.main() == 0
    output = capsys.readouterr().out
    assert "[!!] ambiguous bare library keys: assurance => onedrive.assurance, google.assurance" in output
