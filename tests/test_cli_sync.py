from __future__ import annotations

from lazybooks.cli import sync


def test_sync_runs_index_publish_then_refresh(monkeypatch) -> None:
    calls = []

    def fake_run_step(command):
        calls.append(command)
        return 0

    monkeypatch.setattr(sync, "run_step", fake_run_step)
    monkeypatch.setattr(sync, "command_path", lambda name: name)

    assert sync.main([]) == 0
    assert calls == [
        ["bookindex", "--all", "--publish"],
        ["bookrefresh", "--all"],
    ]


def test_sync_passes_config_to_steps(monkeypatch, tmp_path) -> None:
    calls = []
    config = tmp_path / "config.toml"

    def fake_run_step(command):
        calls.append(command)
        return 0

    monkeypatch.setattr(sync, "run_step", fake_run_step)
    monkeypatch.setattr(sync, "command_path", lambda name: name)

    assert sync.main(["--config", str(config)]) == 0
    assert calls == [
        ["bookindex", "--config", str(config), "--all", "--publish"],
        ["bookrefresh", "--config", str(config), "--all"],
    ]


def test_sync_stops_after_failed_index(monkeypatch) -> None:
    calls = []

    def fake_run_step(command):
        calls.append(command)
        return 7

    monkeypatch.setattr(sync, "run_step", fake_run_step)
    monkeypatch.setattr(sync, "command_path", lambda name: name)

    assert sync.main([]) == 7
    assert calls == [["bookindex", "--all", "--publish"]]
