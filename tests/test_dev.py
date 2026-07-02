"""Adversarial coverage for dev.py: the `check` gate must fail loudly.

A gate that swallowed a failing sub-command would report green while lint or
tests were broken; these cases plant a failure and prove `check` propagates
it and short-circuits.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_dev():
    path = Path(__file__).resolve().parent.parent / "dev.py"
    spec = importlib.util.spec_from_file_location("dev_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dev = _load_dev()


class _FakeCompleted:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def test_unknown_command_returns_2(capsys):
    assert dev.run("nope") == 2
    assert "unknown" in capsys.readouterr().err


def test_check_fails_loudly_and_short_circuits_on_lint_failure(monkeypatch):
    calls = []

    def fake_run(cmd, *a, **k):
        calls.append(cmd)
        return _FakeCompleted(1 if "ruff" in cmd else 0)

    monkeypatch.setattr(dev.subprocess, "run", fake_run)
    assert dev.run("check") != 0
    # A failing lint must not fall through to mypy or pytest.
    assert not any("mypy" in c for c in calls)
    assert not any("pytest" in c for c in calls)


def test_check_runs_full_gate_when_all_green(monkeypatch):
    calls = []

    def fake_run(cmd, *a, **k):
        calls.append(cmd)
        return _FakeCompleted(0)

    monkeypatch.setattr(dev.subprocess, "run", fake_run)
    assert dev.run("check") == 0
    assert any("ruff" in c for c in calls)
    assert any("mypy" in c for c in calls)
    assert any("pytest" in c for c in calls)
