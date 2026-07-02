"""Step 6 fixtures: verify wiring + pending-verify registry for write ops.

Every test uses `stub_client` + `respx_mock` (no real HTTP). Responses are
wrapped in Incus envelope shape so the client's `_handle` unwraps to the
metadata dict verify sees.
"""

from __future__ import annotations

import json

import pytest

import incus_mcp.tools.helpers as helpers
from incus_mcp.tools import read, write


def _sync(metadata):
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": metadata,
    }


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


# ── Sync verify: PUT that echoes the resource ────────────────────────


def test_sync_silent_drop_raises_with_nested_path(stub_client, respx_mock):
    respx_mock.put("/1.0/networks/n0").respond(
        200, json=_sync({"name": "n0", "config": {}}),
    )
    with pytest.raises(ValueError, match=r"config\.ipv4\.address"):
        write.update_network(name="n0", config={"ipv4.address": "10.0.0.1/24"})


def test_sync_verify_pass(stub_client, respx_mock):
    respx_mock.put("/1.0/networks/n0").respond(
        200, json=_sync({"name": "n0", "config": {"ipv4.address": "10.0.0.1/24"}}),
    )
    write.update_network(name="n0", config={"ipv4.address": "10.0.0.1/24"})


# ── Body-builder audit: omit vs explicit-None ─────────────────────────


def test_update_instance_omit_drops_optionals_from_body(stub_client, respx_mock):
    route = respx_mock.put("/1.0/instances/i0").respond(200, json=_sync({}))
    write.update_instance(name="i0")
    body = json.loads(route.calls[0].request.content)
    for k in ("config", "devices", "profiles", "description"):
        assert k not in body


def test_update_instance_explicit_none_passes_as_json_null(stub_client, respx_mock):
    # Mock echoes back the null-valued keys so verify's presence check passes.
    route = respx_mock.put("/1.0/instances/i0").respond(
        200,
        json=_sync({
            "config": None,
            "devices": None,
            "profiles": None,
            "description": None,
        }),
    )
    write.update_instance(
        name="i0",
        config=None,
        devices=None,
        profiles=None,
        description=None,
    )
    body = json.loads(route.calls[0].request.content)
    assert body == {
        "config": None,
        "devices": None,
        "profiles": None,
        "description": None,
    }


def test_update_instance_mixed_omit_and_explicit(stub_client, respx_mock):
    route = respx_mock.put("/1.0/instances/i0").respond(
        200,
        json=_sync({
            "config": {"limits.cpu": "2", "volatile.uuid": "z"},
            "description": None,
        }),
    )
    write.update_instance(name="i0", config={"limits.cpu": "2"}, description=None)
    body = json.loads(route.calls[0].request.content)
    assert body == {"config": {"limits.cpu": "2"}, "description": None}


# ── Query-param drop-both (project on a read op via _qp) ──────────────


def test_list_instances_project_none_drops_qp(stub_client, respx_mock):
    route = respx_mock.get("/1.0/instances").respond(200, json=_sync([]))
    read.list_instances(project=None)
    assert "project" not in str(route.calls[0].request.url)


def test_list_instances_project_empty_drops_qp(stub_client, respx_mock):
    route = respx_mock.get("/1.0/instances").respond(200, json=_sync([]))
    read.list_instances(project="")
    assert "project" not in str(route.calls[0].request.url)


def test_list_instances_project_present(stub_client, respx_mock):
    route = respx_mock.get("/1.0/instances").respond(200, json=_sync([]))
    read.list_instances(project="p")
    assert "project=p" in str(route.calls[0].request.url)


# ── Pending-verify registration ──────────────────────────────────────


def test_create_instance_registers_target_and_qp(stub_client, respx_mock):
    respx_mock.post("/1.0/instances").respond(200, json=_async("op-uuid"))
    write.create_instance(
        name="i0",
        source={"type": "none"},
        project="p",
        target="node2",
    )
    assert "op-uuid" in helpers._pending_verify
    sent, target_path, target_qp, _ = helpers._pending_verify["op-uuid"]
    assert target_path == "/1.0/instances/i0"
    assert target_qp == {"project": "p", "target": "node2"}
    assert sent["name"] == "i0"
    assert sent["source"] == {"type": "none"}


def test_create_instance_no_qp_when_project_omitted(stub_client, respx_mock):
    respx_mock.post("/1.0/instances").respond(200, json=_async("op-noqp"))
    write.create_instance(name="i1", source={"type": "none"})
    _, _, target_qp, _ = helpers._pending_verify["op-noqp"]
    assert target_qp == {}


def test_create_image_from_source_skips_register(stub_client, respx_mock):
    respx_mock.post("/1.0/images").respond(200, json=_async("op-image"))
    write.create_image(source={"type": "url", "url": "http://x"})
    assert "op-image" not in helpers._pending_verify


def test_rename_instance_registers_new_path(stub_client, respx_mock):
    respx_mock.post("/1.0/instances/old").respond(200, json=_async("op-rename"))
    write.rename_instance(name="old", new_name="new")
    assert "op-rename" in helpers._pending_verify
    _, target_path, _, _ = helpers._pending_verify["op-rename"]
    assert target_path == "/1.0/instances/new"


def test_sync_response_does_not_register(stub_client, respx_mock):
    respx_mock.put("/1.0/networks/n0").respond(
        200, json=_sync({"name": "n0", "config": {"x": "y"}}),
    )
    before = set(helpers._pending_verify)
    write.update_network(name="n0", config={"x": "y"})
    assert set(helpers._pending_verify) == before


# ── TTL reap on registration ─────────────────────────────────────────


def test_ttl_reaps_stale_entries_on_next_register(stub_client, respx_mock, monkeypatch):
    current = [1000.0]
    monkeypatch.setattr(helpers.time, "time", lambda: current[0])
    for op_id in ("a", "b", "c"):
        respx_mock.post("/1.0/instances").respond(200, json=_async(op_id))
        write.create_instance(name=f"i-{op_id}", source={"type": "none"})
    assert set(helpers._pending_verify) == {"a", "b", "c"}
    current[0] = 1000.0 + helpers._PENDING_VERIFY_TTL + 1.0
    respx_mock.post("/1.0/instances").respond(200, json=_async("d"))
    write.create_instance(name="i-d", source={"type": "none"})
    assert set(helpers._pending_verify) == {"d"}


# ── Root-skip is root-only; nested keys are real config ──────────────


def test_root_source_is_skipped_at_root(stub_client, respx_mock):
    # create_instance sends `source` at root; the created-resource GET
    # doesn't echo it. Root skip must silence this.
    respx_mock.post("/1.0/instances").respond(
        200,
        json=_sync({"name": "i0", "type": "container"}),
    )
    # No raise:
    write.create_instance(name="i0", source={"type": "image", "alias": "u"})


def test_nested_devices_source_drop_raises(stub_client, respx_mock):
    # `source` inside devices.<name> is a real config value — NOT skipped.
    respx_mock.put("/1.0/instances/i0").respond(
        200, json=_sync({"devices": {"root": {}}}),
    )
    with pytest.raises(ValueError, match=r"devices\.root\.source"):
        write.update_instance(name="i0", devices={"root": {"source": "/dev/xvda"}})
