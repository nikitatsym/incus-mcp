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

from incus_mcp.client import APIError
from incus_mcp.tools import delete, execute, read, write

pytestmark = pytest.mark.integration

_needs_server = pytest.mark.skipif(
    os.environ.get("INCUS_URL") is None, reason="INCUS_URL not set"
)

_SMOKE_SOURCE = {"type": "image", "alias": "images:alpine/3.20"}


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


@_needs_server
async def test_create_and_wait_container():
    name = "mcp-smoke-test"
    op = write.create_instance(name=name, source=_SMOKE_SOURCE, type="container")
    try:
        start = await read.operation_wait_start(op["id"], timeout=120)
        snap = await read.operation_wait_poll(start["wait_id"], max_block=30)
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
        start = await read.operation_wait_start(op["id"], timeout=120)
        snap = await read.operation_wait_poll(start["wait_id"], max_block=30)
        assert snap.get("verify_error") is not None
        assert "nonsense.namespace.key" in snap["verify_error"]
    finally:
        _cleanup(name)
