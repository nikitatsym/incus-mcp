#!/usr/bin/env python3
"""Repo entry point per specs/general/dev-script.md."""
from __future__ import annotations

import subprocess
import sys

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


def run(name: str) -> int:
    if name == "check":
        return run("lint") or run("test")
    if name not in CMDS:
        print(f"unknown: {name}. available: {list(CMDS) + ['check']}", file=sys.stderr)
        return 2
    for cmd in CMDS[name]:
        rc = subprocess.run(cmd).returncode
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else "check"))
