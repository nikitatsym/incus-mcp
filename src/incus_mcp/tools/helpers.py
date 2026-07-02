from __future__ import annotations

import re

from ..client import IncusClient

_client: IncusClient | None = None


def _get_client() -> IncusClient:
    global _client
    if _client is None:
        _client = IncusClient()
    return _client


def _ok(data=None):
    if data is None:
        return {"status": "ok"}
    return data


def _slim(item: dict, fields: set[str]) -> dict:
    out = {}
    for f in fields:
        if "." in f:
            parts = f.split(".", 1)
            val = item.get(parts[0])
            if isinstance(val, dict):
                out[f] = val.get(parts[1])
            else:
                out[f] = None
        else:
            if f in item:
                out[f] = item[f]
    return out


def _slim_list(items, fields: set[str]) -> list[dict]:
    if not isinstance(items, list):
        return items
    return [_slim(i, fields) for i in items]


SLIM_INSTANCE = {"name", "status", "type", "architecture", "location", "project", "created_at"}
SLIM_IMAGE = {"fingerprint", "type", "architecture", "size", "created_at", "properties.description"}
SLIM_NETWORK = {"name", "type", "managed", "status"}
SLIM_VOLUME = {"name", "type", "content_type", "location"}
SLIM_PROFILE = {"name", "description"}
SLIM_PROJECT = {"name", "description"}


def _tail_filter(text: str, tail: int = 100, filter: str | None = None) -> str:
    if not isinstance(text, str) or not text:
        return text
    lines = text.splitlines()
    if filter:
        pattern = re.compile(filter)
        lines = [l for l in lines if pattern.search(l)]
    if tail > 0 and len(lines) > tail:
        truncated = len(lines) - tail
        lines = [f"... ({truncated} lines truncated)"] + lines[-tail:]
    return "\n".join(lines)


def _qp(
    project: str | None = None,
    filter: str | None = None,
    all_projects: bool = False,
    recursion: int | None = None,
    **extra,
) -> dict:
    params = {}
    if project:
        params["project"] = project
    if filter:
        params["filter"] = filter
    if all_projects:
        params["all-projects"] = "true"
    if recursion is not None:
        params["recursion"] = str(recursion)
    for k, v in extra.items():
        if v is not None:
            params[k] = str(v)
    return params


# Root-level only. `devices.root.source` and `devices.disk.mode` are
# real config values, not the top-level transport names.
_SKIP_VERIFY_ROOT: frozenset[str] = frozenset({
    "source", "project", "target", "force", "stateful",
    "uid", "gid", "mode", "file_type", "content",  # file-upload channels
})


def _verify_response(sent: dict, received, path: str = "") -> None:
    """Raise if the API silently dropped a key we sent (recursive).

    Incus returns unknown-key namespaces as an empty dict without a 4xx.
    """
    if not isinstance(received, dict):
        return
    if received.get("class") == "task":
        return  # async op; deferred check runs post-terminal
    for key, value in sent.items():
        if path == "" and key in _SKIP_VERIFY_ROOT:
            continue
        full = f"{path}.{key}" if path else key
        if key not in received:
            raise ValueError(
                f"Incus silently dropped '{full}'. Resource may have been "
                f"created but the field was ignored. Check value format, "
                f"config namespace, or device type."
            )
        if isinstance(value, dict) and value:
            _verify_response(value, received[key], full)
