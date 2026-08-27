"""Expected failures reach the MCP caller as result data, not as exceptions.

An exception crossing the tool boundary is reported by MCP clients as a
contextless execution failure, so the Incus status, body, and failing request
would all be lost. Parameter-validation coverage lives in test_read_help.py and
test_v25_dispatch.py; this file pins the API, transport, root-tool, and
programming-error edges.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

import incus_mcp.wait_registry as wr
from incus_mcp import server
from incus_mcp.registry import Group


@pytest.fixture(autouse=True)
def _reset_wait_registry():
    wr.clear()
    yield
    wr.clear()


def _root_tool(name):
    """The registered ROOT tool, i.e. exactly what an MCP client calls."""
    return server.mcp._tool_manager._tools[name].fn


def _group_tool(name):
    """The registered group tool, i.e. exactly what an MCP client calls."""
    return server.mcp._tool_manager._tools[name].fn


async def test_api_error_reports_status_and_body(stub_client, respx_mock):
    respx_mock.get("/1.0/instances/i0").respond(
        404,
        json={"type": "error", "error_code": 404, "error": "Instance not found"},
    )

    result = await server._dispatch(
        "ShowInstance", "incus_read", {"name": "i0", "project": "must-not-leak"},
    )

    assert "404" in result["error"]
    assert "Instance not found" in result["error"]
    assert "must-not-leak" not in repr(result)


async def test_registered_group_reports_invalid_help_input():
    result = await _group_tool("incus_read")(operation="help", params={"search": 1})

    assert result == {"error": "help parameter 'search' must be a string"}


async def test_transport_error_names_request_without_query(stub_client, respx_mock):
    respx_mock.get("/1.0/instances/i0").mock(
        side_effect=httpx.ConnectError("Connection refused"),
    )

    result = await server._dispatch(
        "ShowInstance", "incus_read", {"name": "i0", "project": "must-not-leak"},
    )

    assert result == {
        "error": (
            "Incus request failed: GET /1.0/instances/i0: "
            "ConnectError: Connection refused"
        )
    }
    assert "must-not-leak" not in repr(result)


async def test_async_waiter_failure_maps_at_await_time(stub_client, respx_mock):
    """The waiter coroutine only fails once awaited - inside the same guard."""
    respx_mock.get("/1.0/operations/op-bad").respond(
        404, json={"type": "error", "error": "not found", "error_code": 404},
    )

    result = await server._dispatch(
        "OperationWaitStart", "incus_read", {"operation_id": "op-bad", "interval": 0.01},
    )

    assert "404" in result["error"]
    assert wr.list_handles() == []


def test_root_version_reports_api_failure(stub_client, respx_mock):
    """incus_version bypasses _dispatch; the registration seam guards it."""
    respx_mock.get("/1.0").respond(
        503, json={"type": "error", "error_code": 503, "error": "server unavailable"},
    )

    result = _root_tool("incus_version")()

    assert "503" in result["error"]
    assert "server unavailable" in result["error"]


def test_root_version_reports_transport_failure(stub_client, respx_mock):
    respx_mock.get("/1.0").mock(side_effect=httpx.ConnectTimeout("timed out"))

    result = _root_tool("incus_version")()

    assert result == {
        "error": "Incus request failed: GET /1.0: ConnectTimeout: timed out"
    }


def test_root_version_keeps_its_success_shape(stub_client, respx_mock):
    respx_mock.get("/1.0").respond(
        200,
        json={
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "metadata": {
                "api_version": "1.0",
                "environment": {"server_name": "incus-1"},
            },
        },
    )

    result = _root_tool("incus_version")()

    assert result["server"] == {"environment": "incus-1", "api_version": "1.0"}


def _failing_op(name: str) -> dict:
    """Synthetic op that hits a bug instead of an expected failure."""
    raise AttributeError("'NoneType' object has no attribute 'get'")


async def test_programming_error_still_propagates(monkeypatch):
    """A bug must stay a crash: only expected failures become result data."""
    _failing_op._mcp_group = Group("incus_read", "")
    server._prepare_op(_failing_op)
    monkeypatch.setitem(server._group_ops["incus_read"], "FailingOp", _failing_op)

    with pytest.raises(AttributeError):
        await server._dispatch("FailingOp", "incus_read", {"name": "x"})


async def test_cancellation_still_propagates_from_registered_group(monkeypatch):
    async def cancelled(name: str) -> dict:
        raise asyncio.CancelledError

    cancelled._mcp_group = Group("incus_read", "")
    server._prepare_op(cancelled)
    monkeypatch.setitem(server._group_ops["incus_read"], "FailingOp", cancelled)

    with pytest.raises(asyncio.CancelledError):
        await _group_tool("incus_read")(operation="FailingOp", params={"name": "x"})
