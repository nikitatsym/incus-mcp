"""Step 7 fixtures: verify short-circuits + no register on state / exec ops."""

from __future__ import annotations

import pytest

import incus_mcp.server as server
import incus_mcp.tools.helpers as helpers
from incus_mcp.tools import execute


def _async(op_id, extra=None):
    op = {
        "id": op_id,
        "class": "task",
        "status": "Running",
        "status_code": 103,
        "metadata": extra or {},
    }
    return {
        "type": "async",
        "status": "Operation created",
        "status_code": 100,
        "operation": f"/1.0/operations/{op_id}",
        "metadata": op,
    }


def _sync(metadata):
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": metadata,
    }


# ── State changes: task response short-circuits inline verify ─────────


def test_start_instance_task_response_no_verify_raise(stub_client, respx_mock):
    respx_mock.put("/1.0/instances/i0/state").respond(200, json=_async("op-start"))
    result = execute.start_instance(name="i0")
    assert isinstance(result, dict) and result.get("class") == "task"


def test_start_instance_does_not_register_pending_verify(stub_client, respx_mock):
    respx_mock.put("/1.0/instances/i0/state").respond(200, json=_async("op-start-2"))
    execute.start_instance(name="i0", project="p")
    assert "op-start-2" not in helpers._pending_verify


def test_stop_instance_force_flag_in_body(stub_client, respx_mock):
    import json
    route = respx_mock.put("/1.0/instances/i0/state").respond(
        200, json=_async("op-stop"),
    )
    execute.stop_instance(name="i0", force=True)
    body = json.loads(route.calls[0].request.content)
    assert body == {"action": "stop", "force": True}


def test_bulk_instance_state_project_qp(stub_client, respx_mock):
    route = respx_mock.put("/1.0/instances").respond(
        200, json=_async("op-bulk"),
    )
    execute.bulk_instance_state(action="restart", project="p")
    assert "project=p" in str(route.calls[0].request.url)
    assert "op-bulk" not in helpers._pending_verify


# ── Exec: task response + no register ─────────────────────────────────


def test_exec_instance_task_response_no_register(stub_client, respx_mock):
    respx_mock.post("/1.0/instances/i0/exec").respond(
        200, json=_async("op-exec"),
    )
    result = execute.exec_instance(
        name="i0",
        command=["bash", "-c", "ls"],
        environment={"K": "V"},
    )
    assert result.get("class") == "task"
    assert "op-exec" not in helpers._pending_verify


def test_exec_instance_omit_optional_fields(stub_client, respx_mock):
    import json
    route = respx_mock.post("/1.0/instances/i0/exec").respond(
        200, json=_async("op-exec-2"),
    )
    execute.exec_instance(name="i0", command=["true"])
    body = json.loads(route.calls[0].request.content)
    assert body["command"] == ["true"]
    assert body["wait-for-websocket"] is False
    assert body["record-output"] is True
    assert body["interactive"] is False
    for k in ("environment", "cwd", "user", "group"):
        assert k not in body


def test_exec_instance_explicit_env_and_cwd(stub_client, respx_mock):
    import json
    route = respx_mock.post("/1.0/instances/i0/exec").respond(
        200, json=_async("op-exec-3"),
    )
    execute.exec_instance(
        name="i0",
        command=["true"],
        environment={"K": "V"},
        cwd="/tmp",
        user=0,
        group=0,
    )
    body = json.loads(route.calls[0].request.content)
    assert body["environment"] == {"K": "V"}
    assert body["cwd"] == "/tmp"
    assert body["user"] == 0
    assert body["group"] == 0


# ── Cluster member state changes: task + no register ──────────────────


def test_evacuate_cluster_member_task(stub_client, respx_mock):
    respx_mock.post("/1.0/cluster/members/node2/state").respond(
        200, json=_async("op-evac"),
    )
    result = execute.evacuate_cluster_member(name="node2")
    assert result.get("class") == "task"
    assert "op-evac" not in helpers._pending_verify


def test_restore_cluster_member_task(stub_client, respx_mock):
    respx_mock.post("/1.0/cluster/members/node2/state").respond(
        200, json=_async("op-restore"),
    )
    result = execute.restore_cluster_member(name="node2")
    assert result.get("class") == "task"


# ── Sync response (rare on state changes but plausible on cluster) ────


def test_sync_response_verify_pass(stub_client, respx_mock):
    respx_mock.post("/1.0/cluster/members/node2/state").respond(
        200, json=_sync({"action": "evacuate", "status": "ok"}),
    )
    execute.evacuate_cluster_member(name="node2")


# ── Adversarial: attack the step's guarantees ─────────────────────────


async def test_bulk_instance_state_invalid_action_rejected(stub_client, respx_mock):
    # Adversarial: Literal must reject before HTTP. Loosening back to `str`
    # would fire the route and fail the assertion.
    route = respx_mock.put("/1.0/instances").respond(200, json=_async("nope"))
    with pytest.raises(ValueError, match="action"):
        await server._dispatch(
            "BulkInstanceState", "incus_execute", {"action": "delete"},
        )
    assert not route.called


async def test_exec_instance_unknown_param_rejected(stub_client, respx_mock):
    # Adversarial: guards `extra='forbid'` on the generated Pydantic model.
    route = respx_mock.post("/1.0/instances/i0/exec").respond(
        200, json=_async("nope"),
    )
    with pytest.raises(ValueError, match="typo_param"):
        await server._dispatch(
            "ExecInstance",
            "incus_execute",
            {"name": "i0", "command": ["true"], "typo_param": "x"},
        )
    assert not route.called


