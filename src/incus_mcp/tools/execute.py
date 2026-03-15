from __future__ import annotations

from ..registry import _op
from .groups import incus_execute
from .helpers import _get_client, _ok


# ── Instance State ───────────────────────────────────────────────────


@_op(incus_execute)
def start_instance(name: str, project: str | None = None):
    """Start an instance."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/instances/{name}/state", json={"action": "start"}, params=params))


@_op(incus_execute)
def stop_instance(name: str, project: str | None = None, force: bool = False):
    """Stop an instance."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/instances/{name}/state", json={"action": "stop", "force": force}, params=params))


@_op(incus_execute)
def restart_instance(name: str, project: str | None = None, force: bool = False):
    """Restart an instance."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/instances/{name}/state", json={"action": "restart", "force": force}, params=params))


@_op(incus_execute)
def freeze_instance(name: str, project: str | None = None):
    """Freeze an instance (pause all processes)."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/instances/{name}/state", json={"action": "freeze"}, params=params))


@_op(incus_execute)
def unfreeze_instance(name: str, project: str | None = None):
    """Unfreeze an instance (resume all processes)."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/instances/{name}/state", json={"action": "unfreeze"}, params=params))


@_op(incus_execute)
def bulk_instance_state(action: str, project: str | None = None):
    """Bulk start/stop/restart all instances. action: start, stop, restart."""
    body: dict = {"action": action}
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put("/1.0/instances", json=body, params=params))


# ── Exec ─────────────────────────────────────────────────────────────


@_op(incus_execute)
def exec_instance(name: str, command: list[str], project: str | None = None,
                  environment: dict | None = None, cwd: str | None = None,
                  user: int | None = None, group: int | None = None):
    """Execute a command in an instance. command: ["bash", "-c", "ls -la"]. Returns operation with output."""
    body: dict = {
        "command": command,
        "wait-for-websocket": False,
        "record-output": True,
        "interactive": False,
    }
    if environment:
        body["environment"] = environment
    if cwd:
        body["cwd"] = cwd
    if user is not None:
        body["user"] = user
    if group is not None:
        body["group"] = group
    params = {}
    if project:
        params["project"] = project
    result = _get_client().post(f"/1.0/instances/{name}/exec", json=body, params=params)
    # Wait for exec to complete and fetch output
    if isinstance(result, dict) and result.get("id"):
        op = _get_client().get(f"/1.0/operations/{result['id']}/wait")
        output = {}
        out = op.get("metadata", {}) if isinstance(op, dict) else {}
        output_files = out.get("output", {})
        for key, path in (output_files.items() if isinstance(output_files, dict) else []):
            try:
                output[key] = _get_client().get(path)
            except Exception:
                pass
        return {
            "return_code": out.get("return"),
            "output": output,
        }
    return result


# ── Cluster Member State ─────────────────────────────────────────────


@_op(incus_execute)
def evacuate_cluster_member(name: str):
    """Evacuate a cluster member (migrate all instances away)."""
    return _ok(_get_client().post(f"/1.0/cluster/members/{name}/state", json={"action": "evacuate"}))


@_op(incus_execute)
def restore_cluster_member(name: str):
    """Restore a cluster member (migrate instances back)."""
    return _ok(_get_client().post(f"/1.0/cluster/members/{name}/state", json={"action": "restore"}))
