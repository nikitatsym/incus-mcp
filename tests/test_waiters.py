"""Step 8 fixtures: async waiters + pending-verify drain (blocking + non-blocking)."""

from __future__ import annotations

import asyncio

import pytest

import incus_mcp.tools.helpers as helpers
import incus_mcp.wait_registry as wr
from incus_mcp.tools import read


def _sync(metadata):
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": metadata,
    }


def _op_body(op_id, status_code=103, status="Running", may_cancel=True):
    return {
        "id": op_id,
        "class": "task",
        "status": status,
        "status_code": status_code,
        "may_cancel": may_cancel,
        "metadata": {},
        "resources": {"instances": [f"/1.0/instances/foo"]},
    }


def _wrap_op(op_id, status_code=103, status="Running"):
    return _sync(_op_body(op_id, status_code, status))


@pytest.fixture(autouse=True)
def _reset_wait_registry():
    wr.clear()
    yield
    wr.clear()


# ── Basic poll behavior ───────────────────────────────────────────────


async def test_running_status_does_not_terminate(stub_client, respx_mock):
    respx_mock.get("/1.0/operations/op-r").respond(
        200, json=_wrap_op("op-r", status_code=103),
    )
    snap = await read.operation_wait_start(
        operation_id="op-r", interval=0.01, timeout=60,
    )
    assert snap["terminated"] is False
    assert snap["status_code"] == 103
    await asyncio.sleep(0.05)
    await read.operation_wait_cancel(wait_id=snap["wait_id"])


async def test_terminal_success_after_two_polls(stub_client, respx_mock):
    import httpx
    # First inline probe: running. Background poll: success.
    responses = [
        _wrap_op("op-t", status_code=103),
        _wrap_op("op-t", status_code=200, status="Success"),
    ]
    respx_mock.get("/1.0/operations/op-t").mock(
        side_effect=lambda req: httpx.Response(200, json=responses.pop(0)),
    )
    snap = await read.operation_wait_start(
        operation_id="op-t", interval=0.01, timeout=60,
    )
    assert snap["terminated"] is False  # first poll still running
    poll = await read.operation_wait_poll(wait_id=snap["wait_id"], max_block=5)
    assert poll["terminated"] is True
    assert poll["status_code"] == 200


async def test_bad_uuid_apierror_propagates_no_handle(stub_client, respx_mock):
    from incus_mcp.client import APIError
    respx_mock.get("/1.0/operations/op-bad").respond(
        404, json={"type": "error", "error": "not found", "error_code": 404},
    )
    with pytest.raises(APIError):
        await read.operation_wait_start(operation_id="op-bad", interval=0.01)
    assert wr.list_handles() == []


async def test_poll_max_block_returns_snapshot_when_running(stub_client, respx_mock):
    respx_mock.get("/1.0/operations/op-p").respond(
        200, json=_wrap_op("op-p", status_code=103),
    )
    snap = await read.operation_wait_start(
        operation_id="op-p", interval=0.01, timeout=60,
    )
    # max_block=0.05: not enough for a terminal transition; snapshot still running.
    poll = await read.operation_wait_poll(wait_id=snap["wait_id"], max_block=0.05)
    assert poll["terminated"] is False
    assert poll["status_code"] == 103
    await read.operation_wait_cancel(wait_id=snap["wait_id"])


async def test_cancel_idempotent(stub_client, respx_mock):
    respx_mock.get("/1.0/operations/op-c").respond(
        200, json=_wrap_op("op-c", status_code=103),
    )
    snap = await read.operation_wait_start(
        operation_id="op-c", interval=0.01, timeout=60,
    )
    first = await read.operation_wait_cancel(wait_id=snap["wait_id"])
    second = await read.operation_wait_cancel(wait_id=snap["wait_id"])
    assert first["wait_id"] == snap["wait_id"]
    assert second["wait_id"] == snap["wait_id"]


async def test_waits_list_reaps_expired(stub_client, respx_mock, monkeypatch):
    respx_mock.get("/1.0/operations/op-w").respond(
        200, json=_wrap_op("op-w", status_code=200, status="Success"),
    )
    # Terminal on first poll -> handle immediately gets ended_at.
    snap = await read.operation_wait_start(
        operation_id="op-w", interval=0.01, timeout=60,
    )
    assert snap["terminated"] is True
    # Push time past TTL.
    handle = wr.get_handle(snap["wait_id"])
    assert handle is not None
    handle.ended_at = handle.ended_at - (wr._DEFAULT_TTL_SECONDS + 10)
    listed = await read.waits_list()
    assert listed == []  # reaped opportunistically


# ── Post-terminal verify drain (adversarial: silent-drop) ─────────────


async def test_verify_drain_silent_drop_populates_verify_error(stub_client, respx_mock):
    # Register manually - simulates what create_instance did in a prior tool call.
    helpers._pending_verify["op-drop"] = (
        {"config": {"limits.cpu": "2"}},
        "/1.0/instances/foo",
        {},
        __import__("time").time(),
    )
    respx_mock.get("/1.0/operations/op-drop").respond(
        200, json=_wrap_op("op-drop", status_code=200, status="Success"),
    )
    respx_mock.get("/1.0/instances/foo").respond(
        200, json=_sync({"name": "foo", "config": {}}),
    )
    snap = await read.operation_wait_start(
        operation_id="op-drop", interval=0.01, timeout=60,
    )
    assert snap["terminated"] is True
    assert snap["verify_error"] is not None
    assert "config.limits.cpu" in snap["verify_error"]
    assert "op-drop" not in helpers._pending_verify


async def test_verify_drain_pass_leaves_error_none(stub_client, respx_mock):
    helpers._pending_verify["op-pass"] = (
        {"config": {"limits.cpu": "2"}},
        "/1.0/instances/bar",
        {},
        __import__("time").time(),
    )
    respx_mock.get("/1.0/operations/op-pass").respond(
        200, json=_wrap_op("op-pass", status_code=200, status="Success"),
    )
    respx_mock.get("/1.0/instances/bar").respond(
        200, json=_sync({"config": {"limits.cpu": "2", "volatile.uuid": "z"}}),
    )
    snap = await read.operation_wait_start(
        operation_id="op-pass", interval=0.01, timeout=60,
    )
    assert snap["terminated"] is True
    assert snap["verify_error"] is None
    assert "op-pass" not in helpers._pending_verify


async def test_failed_operation_skips_drain(stub_client, respx_mock):
    helpers._pending_verify["op-fail"] = (
        {"config": {"x": "y"}},
        "/1.0/instances/fail",
        {},
        __import__("time").time(),
    )
    respx_mock.get("/1.0/operations/op-fail").respond(
        200, json=_wrap_op("op-fail", status_code=400, status="Failure"),
    )
    # Route on target NOT expected to fire.
    target_route = respx_mock.get("/1.0/instances/fail").respond(
        200, json=_sync({"config": {"x": "y"}}),
    )
    snap = await read.operation_wait_start(
        operation_id="op-fail", interval=0.01, timeout=60,
    )
    assert snap["terminated"] is True
    assert snap["status_code"] == 400
    assert snap["verify_error"] is None
    # Failed op: drain skipped, entry STAYS until TTL (per plan §6b).
    assert "op-fail" in helpers._pending_verify
    assert not target_route.called


async def test_enrichment_blip_populates_enrichment_error(stub_client, respx_mock):
    helpers._pending_verify["op-blip"] = (
        {"config": {"limits.cpu": "2"}},
        "/1.0/instances/blip",
        {},
        __import__("time").time(),
    )
    respx_mock.get("/1.0/operations/op-blip").respond(
        200, json=_wrap_op("op-blip", status_code=200, status="Success"),
    )
    respx_mock.get("/1.0/instances/blip").respond(
        500, json={"type": "error", "error": "boom", "error_code": 500},
    )
    snap = await read.operation_wait_start(
        operation_id="op-blip", interval=0.01, timeout=60,
    )
    assert snap["terminated"] is True
    assert snap["verify_error"] is None
    assert snap["enrichment_error"] is not None
    assert "500" in snap["enrichment_error"]


# ── Blocking wait_operation drain (adversarial: raises on drop) ───────


def test_blocking_wait_operation_drain_raises_on_drop(stub_client, respx_mock):
    helpers._pending_verify["op-blk"] = (
        {"config": {"limits.cpu": "2"}},
        "/1.0/instances/blk",
        {},
        __import__("time").time(),
    )
    respx_mock.get("/1.0/operations/op-blk/wait").respond(
        200, json=_wrap_op("op-blk", status_code=200, status="Success"),
    )
    respx_mock.get("/1.0/instances/blk").respond(
        200, json=_sync({"name": "blk", "config": {}}),
    )
    with pytest.raises(ValueError, match=r"config\.limits\.cpu"):
        read.wait_operation(id="op-blk")


def test_blocking_wait_operation_success_no_pending_no_raise(stub_client, respx_mock):
    respx_mock.get("/1.0/operations/op-blk2/wait").respond(
        200, json=_wrap_op("op-blk2", status_code=200, status="Success"),
    )
    result = read.wait_operation(id="op-blk2")
    assert result["status_code"] == 200
