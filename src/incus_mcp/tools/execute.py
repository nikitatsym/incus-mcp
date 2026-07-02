from __future__ import annotations

from typing import Annotated, Literal, cast

from pydantic import Field

from ..registry import _UNSET, _op
from .groups import incus_execute
from .helpers import (
    _FORCE_DESC,
    _PROJECT_DESC,
    _get_client,
    _ok,
    _qp,
    _verify_response,
)

# State changes and exec are always async; no register - target GET has
# no action-verb field to check against (plan 7b).

_ProjectAnn = Annotated[str | None, Field(description=_PROJECT_DESC)]
_UNSET_STR = cast(str | None, _UNSET)
_UNSET_DICT = cast(dict | None, _UNSET)
_UNSET_INT = cast(int | None, _UNSET)


# ── Instance State ───────────────────────────────────────────────────


@_op(incus_execute)
def start_instance(name: str, project: _ProjectAnn = _UNSET_STR):
    """Start an instance. Returns an async operation."""
    body: dict = {"action": "start"}
    result = _get_client().put(
        f"/1.0/instances/{name}/state", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_execute)
def stop_instance(
    name: str,
    project: _ProjectAnn = _UNSET_STR,
    force: Annotated[bool, Field(description=_FORCE_DESC)] = False,
):
    """Stop an instance. Returns an async operation."""
    body: dict = {"action": "stop", "force": force}
    result = _get_client().put(
        f"/1.0/instances/{name}/state", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_execute)
def restart_instance(
    name: str,
    project: _ProjectAnn = _UNSET_STR,
    force: Annotated[bool, Field(description=_FORCE_DESC)] = False,
):
    """Restart an instance. Returns an async operation."""
    body: dict = {"action": "restart", "force": force}
    result = _get_client().put(
        f"/1.0/instances/{name}/state", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_execute)
def freeze_instance(name: str, project: _ProjectAnn = _UNSET_STR):
    """Freeze an instance (pause all processes). Returns an async operation."""
    body: dict = {"action": "freeze"}
    result = _get_client().put(
        f"/1.0/instances/{name}/state", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_execute)
def unfreeze_instance(name: str, project: _ProjectAnn = _UNSET_STR):
    """Unfreeze an instance (resume all processes). Returns an async operation."""
    body: dict = {"action": "unfreeze"}
    result = _get_client().put(
        f"/1.0/instances/{name}/state", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_execute)
def bulk_instance_state(
    action: Annotated[
        Literal["start", "stop", "restart"],
        Field(description="Bulk-apply the action to every instance in the project."),
    ],
    project: _ProjectAnn = _UNSET_STR,
):
    """Bulk start / stop / restart every instance in the project. Async."""
    body: dict = {"action": action}
    result = _get_client().put(
        "/1.0/instances", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


# ── Exec ─────────────────────────────────────────────────────────────


@_op(incus_execute)
def exec_instance(
    name: str,
    command: Annotated[
        list[str],
        Field(
            description=(
                "Argv list (e.g. ['bash', '-c', 'ls -la']). Returns the operation "
                "object with record-output enabled; use ListExecOutputs / "
                "GetExecOutput to read stdout/stderr."
            ),
        ),
    ],
    project: _ProjectAnn = _UNSET_STR,
    environment: Annotated[dict | None, Field(description="Extra env vars for the command.")] = _UNSET_DICT,
    cwd: Annotated[str | None, Field(description="Working directory inside the instance.")] = _UNSET_STR,
    user: Annotated[int | None, Field(description="UID to run as (default is the instance's root user).")] = _UNSET_INT,
    group: Annotated[int | None, Field(description="GID to run as.")] = _UNSET_INT,
):
    """Execute a command in an instance. Returns the operation ID immediately."""
    body: dict = {
        "command": command,
        "wait-for-websocket": False,
        "record-output": True,
        "interactive": False,
    }
    if environment is not _UNSET:
        body["environment"] = environment
    if cwd is not _UNSET:
        body["cwd"] = cwd
    if user is not _UNSET:
        body["user"] = user
    if group is not _UNSET:
        body["group"] = group
    result = _get_client().post(
        f"/1.0/instances/{name}/exec", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return result


# ── Cluster Member State ─────────────────────────────────────────────


@_op(incus_execute)
def evacuate_cluster_member(name: str):
    """Evacuate a cluster member (migrate all instances away). Async."""
    body: dict = {"action": "evacuate"}
    result = _get_client().post(
        f"/1.0/cluster/members/{name}/state", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_execute)
def restore_cluster_member(name: str):
    """Restore a cluster member (migrate instances back). Async."""
    body: dict = {"action": "restore"}
    result = _get_client().post(
        f"/1.0/cluster/members/{name}/state", json=body,
    )
    _verify_response(body, result)
    return _ok(result)
