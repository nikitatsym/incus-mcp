"""Integration smoke tests against a real Incus server.

Excluded from the default suite (`addopts = -m 'not integration'`); run with
`uv run python dev.py e2e`. Every case is additionally skipped unless
`INCUS_URL` is set, so `-m integration` without a server is a clean skip
rather than a connection error. Auth env (TLS cert or OIDC vars) must also
be present for these to pass; see the README install section.
"""

from __future__ import annotations

import os

import pytest

from incus_mcp import server
from incus_mcp.client import APIError
from incus_mcp.tools import delete, execute, read, write

pytestmark = pytest.mark.integration

_needs_server = pytest.mark.skipif(
    os.environ.get("INCUS_URL") is None, reason="INCUS_URL not set"
)

_SMOKE_SOURCE = {"type": "image", "alias": "e2e-alpine"}


def _settle(result: object) -> None:
    """Block until an async operation result terminates; no-op for sync results."""
    if isinstance(result, dict) and result.get("class") == "task" and result.get("id"):
        read.wait_operation(str(result["id"]))


def _cleanup(name: str) -> None:
    """Best-effort teardown: stop then delete, waiting for each op to finish.

    Waiting between stop and delete matters: delete against a still-stopping
    instance is a 400, which would leak the smoke instance on the server.
    """
    try:
        _settle(execute.stop_instance(name, force=True))
    except APIError:
        pass
    try:
        _settle(delete.delete_instance(name))
    except APIError:
        pass


def _create_and_start(name: str) -> None:
    """Create a container from the smoke image and start it (both ops waited)."""
    _settle(write.create_instance(name=name, source=_SMOKE_SOURCE, type="container"))
    _settle(execute.start_instance(name))


@_needs_server
async def test_create_and_wait_container():
    name = "mcp-smoke-test"
    op = write.create_instance(name=name, source=_SMOKE_SOURCE, type="container")
    try:
        start = await read.operation_wait_start(op["id"], timeout=180)
        snap = await read.operation_wait_poll(start["wait_id"], max_block=150)
        assert snap["terminated"]
        assert snap["status_code"] == 200
        assert snap.get("verify_error") is None
    finally:
        _cleanup(name)


@_needs_server
def test_silent_drop_verify_sync():
    # Bogus key against a real managed network: the server rejects it
    # (APIError) or accepts-and-drops it (ValueError from _verify_response) -
    # either proves no silent success. PATCH (merge), not a full-replace PUT,
    # so the network's live config is never wiped.
    managed = [n for n in read.list_networks() if n.get("managed")]
    if not managed:
        pytest.skip("no managed network to target")
    with pytest.raises((APIError, ValueError)):
        write.patch_network(name=managed[0]["name"], config={"nonsense.key": "x"})


@_needs_server
async def test_silent_drop_verify_async():
    name = "mcp-smoke-badcfg"
    op = write.create_instance(
        name=name,
        source=_SMOKE_SOURCE,
        type="container",
        config={"nonsense.namespace.key": "x"},
    )
    try:
        start = await read.operation_wait_start(op["id"], timeout=180)
        snap = await read.operation_wait_poll(start["wait_id"], max_block=150)
        # No phantom success: real Incus either fails the operation outright
        # (terminal status_code >= 400) or accepts it and silently drops the
        # bogus key (surfaced post-terminal as verify_error). Both are loud;
        # Incus 6.0 rejects an unknown config namespace with a 400.
        failed = bool(snap.get("terminated")) and (snap.get("status_code") or 0) >= 400
        assert failed or snap.get("verify_error") is not None, snap
        if snap.get("verify_error") is not None:
            assert "nonsense.namespace.key" in snap["verify_error"]
    finally:
        _cleanup(name)


@_needs_server
def test_exec_output_roundtrip():
    # One case covers exec + blocking wait + exec-output logs: run `echo hi` in
    # a started container, wait for the op, read the recorded stdout back.
    # Blocking wait_operation, not the interval poller: a fast exec op is reaped
    # by Incus before an interval poll would observe terminal success.
    name = "mcp-smoke-exec"
    _create_and_start(name)
    try:
        op = execute.exec_instance(name, command=["echo", "hi"])
        result = read.wait_operation(op["id"])
        assert result.get("status_code") == 200
        outputs = read.list_exec_outputs(name)
        stdout = [f for f in outputs if "stdout" in f]
        assert stdout, outputs
        text = read.get_exec_output(name, stdout[0].rsplit("/", 1)[-1])
        assert "hi" in text
    finally:
        _cleanup(name)


@_needs_server
async def test_create_via_dispatch():
    # Same create, but through the MCP dispatch layer (Pydantic params model +
    # coerce), not the bare tool fn - covers the "bypassing the server" gap.
    name = "mcp-smoke-dispatch"
    op = await server._dispatch(
        "CreateInstance",
        "incus_write",
        {"name": name, "source": _SMOKE_SOURCE, "type": "container"},
    )
    try:
        start = await read.operation_wait_start(op["id"], timeout=180)
        snap = await read.operation_wait_poll(start["wait_id"], max_block=150)
        assert snap["terminated"] and snap["status_code"] == 200
    finally:
        _cleanup(name)


@_needs_server
async def test_wait_cancel_live():
    # Cancel the local poll of a genuinely long op (30s sleep exec) while it is
    # still running: the wait ends without the operation terminating, and a
    # second cancel is a no-op.
    name = "mcp-smoke-cancel"
    _create_and_start(name)
    try:
        op = execute.exec_instance(name, command=["sleep", "30"])
        start = await read.operation_wait_start(op["id"], timeout=60, interval=2)
        snap = await read.operation_wait_cancel(start["wait_id"])
        assert not snap["terminated"]
        await read.operation_wait_cancel(start["wait_id"])  # idempotent
    finally:
        _cleanup(name)
