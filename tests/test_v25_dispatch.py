"""Step 4 fixtures: v2.5 dispatch core (_build_params_model, _dispatch,
_build_help, _build_schema, _make_tool) against a tiny synthetic group."""

from __future__ import annotations

import json
from typing import Annotated, cast

import pytest
from pydantic import Field

import incus_mcp.server as server
from incus_mcp.registry import _UNSET, Group

GROUP = "test_group"

_received: list[dict] = []


def first_op(name: str) -> dict:
    """Create a thing."""
    return {"name": name}


def second_op(
    tag: Annotated[str | None, Field(description="Tag to attach.")] = cast(
        "str | None", _UNSET
    ),
) -> dict:
    """List things.

    Extra context line that should render indented under the signature.
    """
    kwargs = {} if tag is _UNSET else {"tag": tag}
    _received.append(kwargs)
    return kwargs


async def fake_wait(x: int = 0) -> dict:
    """Wait for a fake thing."""
    return {"x": x}


@pytest.fixture
def tiny_group(monkeypatch):
    _received.clear()
    group = Group(GROUP, "Synthetic group for dispatch tests.")
    ops = {}
    for fn in (first_op, second_op, fake_wait):
        fn._mcp_group = group
        server._prepare_op(fn)
        ops[server._to_pascal(fn.__name__)] = fn
    monkeypatch.setitem(server._group_ops, GROUP, ops)
    for pascal in ops:
        monkeypatch.setitem(server._all_grouped, pascal, GROUP)
    return ops


async def test_help_shows_ops_marker_and_bullet(tiny_group):
    out = await server._dispatch("help", GROUP, {})
    assert "FirstOp(name: str)" in out
    assert "SecondOp(tag?: str | None)" in out
    assert "Create a thing." in out
    assert "    tag: Tag to attach." in out
    assert "    Extra context line" in out
    assert "_Unset" not in out
    assert "_UNSET" not in out


async def test_schema_via_dispatch(tiny_group):
    first = await server._dispatch("schema", GROUP, {"op": "FirstOp"})
    assert first["additionalProperties"] is False
    assert first["required"] == ["name"]
    second = await server._dispatch("schema", GROUP, {"op": "SecondOp"})
    assert second["properties"]["tag"]["description"] == "Tag to attach."
    assert "_Unset" not in json.dumps(second)


def test_build_schema_direct(tiny_group):
    via_helper = server._build_schema(GROUP, "FirstOp")
    assert via_helper["additionalProperties"] is False
    assert via_helper["required"] == ["name"]


async def test_schema_without_op_lists_names(tiny_group):
    out = await server._dispatch("schema", GROUP, {})
    assert out == ["FakeWait", "FirstOp", "SecondOp"]


async def test_unknown_op_names_available(tiny_group):
    with pytest.raises(ValueError, match="FirstOp"):
        await server._dispatch("NoSuchOp", GROUP, {})


async def test_unknown_param_points_at_schema(tiny_group):
    with pytest.raises(ValueError, match="foo") as exc:
        await server._dispatch("FirstOp", GROUP, {"name": "x", "foo": "bar"})
    assert "operation='schema'" in str(exc.value)


async def test_missing_required_param(tiny_group):
    with pytest.raises(ValueError, match="name"):
        await server._dispatch("FirstOp", GROUP, {})


async def test_meta_tool_no_mutable_default_leak(tiny_group):
    tool_fn = server._make_tool(GROUP, "doc")
    assert await tool_fn("SecondOp") == {}
    assert await tool_fn("SecondOp", {"tag": "x"}) == {"tag": "x"}
    assert await tool_fn("SecondOp") == {}
    assert _received == [{}, {"tag": "x"}, {}]


async def test_async_op_is_awaited(tiny_group):
    result = await server._dispatch("FakeWait", GROUP, {"x": 2})
    assert result == {"x": 2}


async def test_wrong_group_hint(tiny_group):
    with pytest.raises(ValueError, match="incus_read"):
        await server._dispatch("ListInstances", GROUP, {})


def test_real_registry_help_renders():
    out = server._build_help("incus_read")
    assert "ListInstances(" in out
    assert "_Unset" not in out
