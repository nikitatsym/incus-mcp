#!/usr/bin/env python3
"""Repo entry point per specs/general/dev-script.md."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

CMDS: dict[str, list[list[str]]] = {
    "lint": [
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "mypy", "src/"],
    ],
    "test": [
        ["uv", "run", "pytest"],
    ],
    "e2e": [
        ["uv", "run", "pytest", "-m", "integration"],
    ],
}


def install_hook() -> int:
    """Point git at the repo's tracked pre-commit hook. Idempotent."""
    root = Path(__file__).resolve().parent
    if (root / ".githooks" / "pre-commit").exists():
        return subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"], check=False
        ).returncode
    print("no tracked hook: expected .githooks/pre-commit", file=sys.stderr)
    return 1


def _hook_ready() -> bool:
    root = Path(__file__).resolve().parent
    if (root / ".git" / "hooks" / "pre-commit").exists():
        return True
    configured = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return bool(configured) and (root / configured / "pre-commit").exists()


def _hook_hint() -> None:
    # A fresh clone gates nothing until asked; CI has no use for a hook.
    if not os.environ.get("CI") and not _hook_ready():
        print("hint: `python dev.py hook` installs the pre-commit gate", file=sys.stderr)


def run(name: str) -> int:
    if name == "hook":
        return install_hook()
    if name == "check":
        _hook_hint()
        return run("lint") or run("test")
    if name not in CMDS:
        print(f"unknown: {name}. available: {list(CMDS) + ['check', 'hook']}", file=sys.stderr)
        return 2
    for cmd in CMDS[name]:
        rc = subprocess.run(cmd, check=False).returncode
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else "check"))
