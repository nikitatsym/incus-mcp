from __future__ import annotations

import re
import time
from typing import Any

from ..client import IncusClient
from ..registry import _UNSET, _Unset

_client: IncusClient | None = None


# ── Shared Field descriptions (used across read/write/execute/delete) ────

_PROJECT_DESC = "Incus project (default project when omitted)."
_API_FILTER_DESC = (
    "Incus API filter expression (e.g. 'status eq Running,type eq container')."
)
_REGEX_FILTER_DESC = "Regex applied line by line before tail."
_TAIL_DESC = "Return last N lines (0 = full content)."
_ALL_PROJECTS_DESC = "List across every project the caller can see."
_VOLUME_TYPE_DESC = (
    "Filter by volume type (custom, container, image, virtual-machine)."
)

_DESCRIPTION_DESC = "Human-readable description of the resource."
_TARGET_DESC = "Target cluster member for placement (cluster deployments only)."
_CONFIG_DESC = (
    "Config namespace map (e.g. {'limits.cpu': '2', 'limits.memory': '4GiB'}). "
    "See Incus API for allowed keys per resource."
)
_DEVICES_DESC = (
    "Device map keyed by device name (e.g. {'eth0': {'type': 'nic', "
    "'nictype': 'bridged', 'parent': 'incusbr0'}}). See Incus API for "
    "device type schemas."
)
_PROFILES_DESC = (
    "Profile names to apply in order (later profiles override earlier)."
)
_STATEFUL_DESC = "Include runtime memory state (VM only, ignored for containers)."
_SOURCE_INSTANCE_DESC = (
    "Source spec: {'type': 'image', 'alias': 'ubuntu/24.04'}, "
    "{'type': 'copy', 'source': 'other-instance'}, or {'type': 'none'} "
    "for empty. See Incus API docs for full types."
)
_SOURCE_IMAGE_DESC = (
    "Image source spec: {'type': 'url', 'url': '...'}, "
    "{'type': 'instance', 'name': '...'}, or {'type': 'snapshot', ...}."
)
_FORCE_DESC = "Immediate kill instead of graceful shutdown."


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
    project: str | _Unset | None = None,
    filter: str | _Unset | None = None,
    all_projects: bool = False,
    recursion: int | None = None,
    **extra: Any,
) -> dict[str, str]:
    """Build a query-param dict; drops `_UNSET`, None, and empty strings.

    `all_projects=True` renders as `all-projects=true`; `recursion=<int>`
    always renders (0 is meaningful); everything else `str(v)`-coerces.
    Named params are typed for mypy; `**extra` carries op-specific keys
    like `type=` (screenshot) or `path=` (file fetch).
    """
    params: dict[str, str] = {}
    if project is not _UNSET and project is not None and project != "":
        params["project"] = str(project)
    if filter is not _UNSET and filter is not None and filter != "":
        params["filter"] = str(filter)
    if all_projects:
        params["all-projects"] = "true"
    if recursion is not None:
        params["recursion"] = str(recursion)
    for k, v in extra.items():
        if v is _UNSET or v is None or v == "":
            continue
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


# ── Pending-verify registry for async writes ────────────────────────────
#
# Async write ops (POST returning class="task") register (sent, target_path,
# target_query_params, ts) here keyed by op id. The waiter (Step 8) drains
# on terminal success by fetching the target and running _verify_response.
# Entries survive across MCP tool calls (write happens now, wait later) but
# NOT process restart. TTL prevents unbounded growth if wait is never called.

_pending_verify: dict[str, tuple[dict, str, dict[str, str], float]] = {}
_PENDING_VERIFY_TTL = 3600.0


def _register_pending_verify(
    result: Any,
    sent: dict,
    target_path: str,
    target_query_params: dict[str, str] | None = None,
) -> None:
    """Register a verify-context for an async write. No-op if not a task."""
    if not isinstance(result, dict) or result.get("class") != "task":
        return
    op_id = result.get("id")
    if not op_id:
        return
    now = time.time()
    stale = [k for k, (_, _, _, ts) in _pending_verify.items() if now - ts > _PENDING_VERIFY_TTL]
    for k in stale:
        _pending_verify.pop(k, None)
    _pending_verify[op_id] = (sent, target_path, dict(target_query_params or {}), now)


def _drain_pending_verify(op_id: str) -> tuple[dict, str, dict[str, str]] | None:
    """Pop and return the entry for `op_id`, or None if absent/already drained."""
    entry = _pending_verify.pop(op_id, None)
    if entry is None:
        return None
    sent, target_path, target_qp, _ = entry
    return sent, target_path, target_qp
