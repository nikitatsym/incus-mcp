#!/usr/bin/env python3
"""Vendor Incus's swagger 2.0 spec for the conformance test.

Incus publishes `doc/rest-api.yaml` in its source tree only - no running
daemon serves it - so the conformance test reads a pinned copy from
`tests/data/`. YAML is converted to JSON here so the test needs no YAML
parser at gate time; the document is otherwise carried through untouched
apart from the `x-source` provenance block.

    uv run --with pyyaml python scripts/fetch-incus-spec.py v7.3.0
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import yaml

RAW_URL = "https://raw.githubusercontent.com/lxc/incus/{tag}/doc/rest-api.yaml"
OUT = Path(__file__).resolve().parent.parent / "tests" / "data" / "incus-rest-api.json"


def main(tag: str) -> int:
    url = RAW_URL.format(tag=tag)
    response = httpx.get(url, follow_redirects=True, timeout=60.0)
    response.raise_for_status()
    spec = yaml.safe_load(response.text)
    spec["x-source"] = {"repo": "lxc/incus", "tag": tag, "url": url}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(spec, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT} from {url} ({len(spec['paths'])} paths)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <incus-git-tag>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
