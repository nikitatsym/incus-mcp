"""TypedDicts for Incus API response shapes and wait-handle snapshots.

Applied at the client->tools boundary: `_handle()` returns `Any`; each op
declares the shape it expects and mypy checks the wire-schema at every
tool call. Fields marked `NotRequired` are the ones Incus omits under some
API paths (e.g. `location` only in cluster mode).
"""

from __future__ import annotations

from typing import Any, TypedDict

from typing_extensions import NotRequired


# ── Async operation object (any /1.0/operations/... response) ──────────


class OperationDict(TypedDict):
    id: str
    class_: NotRequired[str]  # Incus wire uses `class`; renamed here (see below)
    description: NotRequired[str]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]
    status: NotRequired[str]
    status_code: NotRequired[int]
    resources: NotRequired[dict[str, Any]]
    metadata: NotRequired[dict[str, Any] | None]
    may_cancel: NotRequired[bool]
    err: NotRequired[str]
    location: NotRequired[str]


# NOTE: Incus wire uses the reserved word `class`. TypedDict class syntax
# cannot declare a `class` key, so any code reading the field goes via
# `dict.get("class")` on the raw dict; `OperationDict` documents the shape
# without renaming.


# ── Instance ───────────────────────────────────────────────────────────


class InstanceDict(TypedDict):
    name: str
    architecture: NotRequired[str]
    config: NotRequired[dict[str, Any]]
    devices: NotRequired[dict[str, Any]]
    ephemeral: NotRequired[bool]
    profiles: NotRequired[list[str]]
    stateful: NotRequired[bool]
    description: NotRequired[str]
    created_at: NotRequired[str]
    expanded_config: NotRequired[dict[str, Any]]
    expanded_devices: NotRequired[dict[str, Any]]
    status: NotRequired[str]
    status_code: NotRequired[int]
    last_used_at: NotRequired[str]
    location: NotRequired[str]
    type: NotRequired[str]
    project: NotRequired[str]


class SlimInstanceDict(TypedDict):
    name: NotRequired[str]
    status: NotRequired[str]
    type: NotRequired[str]
    architecture: NotRequired[str]
    location: NotRequired[str]
    project: NotRequired[str]
    created_at: NotRequired[str]


# ── Image ──────────────────────────────────────────────────────────────


class ImageDict(TypedDict):
    fingerprint: str
    type: NotRequired[str]
    architecture: NotRequired[str]
    size: NotRequired[int]
    created_at: NotRequired[str]
    uploaded_at: NotRequired[str]
    last_used_at: NotRequired[str]
    expires_at: NotRequired[str]
    public: NotRequired[bool]
    auto_update: NotRequired[bool]
    properties: NotRequired[dict[str, Any]]
    aliases: NotRequired[list[dict[str, Any]]]
    profiles: NotRequired[list[str]]
    project: NotRequired[str]
    update_source: NotRequired[dict[str, Any]]


class SlimImageDict(TypedDict, total=False):
    fingerprint: str
    type: str
    architecture: str
    size: int
    created_at: str
    # From SLIM_IMAGE `properties.description` - the sliminfo builder
    # writes the flattened key `properties.description` verbatim.


# ── Network ────────────────────────────────────────────────────────────


class NetworkDict(TypedDict):
    name: str
    type: NotRequired[str]
    managed: NotRequired[bool]
    status: NotRequired[str]
    description: NotRequired[str]
    config: NotRequired[dict[str, Any]]
    used_by: NotRequired[list[str]]
    locations: NotRequired[list[str]]
    project: NotRequired[str]


class SlimNetworkDict(TypedDict, total=False):
    name: str
    type: str
    managed: bool
    status: str


# ── Volume ─────────────────────────────────────────────────────────────


class VolumeDict(TypedDict):
    name: str
    type: NotRequired[str]
    content_type: NotRequired[str]
    description: NotRequired[str]
    config: NotRequired[dict[str, Any]]
    location: NotRequired[str]
    pool: NotRequired[str]
    project: NotRequired[str]
    used_by: NotRequired[list[str]]
    created_at: NotRequired[str]


class SlimVolumeDict(TypedDict, total=False):
    name: str
    type: str
    content_type: str
    location: str


# ── Profile ────────────────────────────────────────────────────────────


class ProfileDict(TypedDict):
    name: str
    description: NotRequired[str]
    config: NotRequired[dict[str, Any]]
    devices: NotRequired[dict[str, Any]]
    used_by: NotRequired[list[str]]
    project: NotRequired[str]


class SlimProfileDict(TypedDict, total=False):
    name: str
    description: str


# ── Project ────────────────────────────────────────────────────────────


class ProjectDict(TypedDict):
    name: str
    description: NotRequired[str]
    config: NotRequired[dict[str, Any]]
    used_by: NotRequired[list[str]]


class SlimProjectDict(TypedDict, total=False):
    name: str
    description: str


# ── Warning ────────────────────────────────────────────────────────────


class WarningDict(TypedDict):
    uuid: str
    status: NotRequired[str]
    type_code: NotRequired[int]
    severity_code: NotRequired[int]
    entity_url: NotRequired[str]
    project: NotRequired[str]
    location: NotRequired[str]
    first_seen_at: NotRequired[str]
    last_seen_at: NotRequired[str]
    updated_at: NotRequired[str]
    count: NotRequired[int]
    last_message: NotRequired[str]


# ── Wait-handle snapshots ──────────────────────────────────────────────
#
# `WaitTransitionDict` MUST use the functional form: the key `"from"` is a
# Python keyword, class syntax can't declare it.

WaitTransitionDict = TypedDict(
    "WaitTransitionDict",
    {
        "from": "str | None",
        "to": "str | None",
        "status_code": "int | None",
        "elapsed_seconds": float,
    },
)


class WaitSnapshotDict(TypedDict):
    """Mirrors `WaitHandle.snapshot()` exactly.

    Required keys are unconditional; `NotRequired` keys are set by the
    handle only under specific conditions (poll failures, last payload,
    terminal error).
    """

    wait_id: str
    operation_id: str
    status: str | None
    status_code: int | None
    terminated: bool
    timed_out: bool
    polls: int
    elapsed_seconds: float
    started_at: float
    ended_at: float | None
    transitions: list[WaitTransitionDict]
    verify_error: str | None
    enrichment_error: str | None
    poll_failures: NotRequired[int]
    last_poll_error: NotRequired[str | None]
    operation: NotRequired[OperationDict]
    error: NotRequired[str]
