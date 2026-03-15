from __future__ import annotations

import inspect
import pkgutil
import typing

from mcp.server.fastmcp import FastMCP

from . import tools as _tools_pkg
from .registry import ROOT

mcp = FastMCP("incus")

_group_ops: dict[str, dict[str, typing.Callable]] = {}
_all_grouped: dict[str, str] = {}


def _to_pascal(name: str) -> str:
    return "".join(w.capitalize() for w in name.split("_"))


def _is_bool_hint(hint) -> bool:
    if hint is bool:
        return True
    origin = getattr(hint, "__origin__", None)
    if origin is typing.Union:
        return bool in hint.__args__
    return False


def _parse_bool(val, default=None):
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val)


def _coerce_call(fn, params: dict):
    hints = typing.get_type_hints(fn)
    coerced = {}
    for k, v in params.items():
        if k in hints and _is_bool_hint(hints[k]):
            v = _parse_bool(v)
        coerced[k] = v
    return fn(**coerced)


def _build_help(group_name: str) -> str:
    ops = _group_ops.get(group_name, {})
    lines = [f"{len(ops)} operations available:"]
    for pascal_name, fn in sorted(ops.items()):
        sig = inspect.signature(fn)
        params = ", ".join(
            f"{p.name}" + (f"={p.default!r}" if p.default is not inspect.Parameter.empty else "")
            for p in sig.parameters.values()
        )
        doc = (fn.__doc__ or "").split("\n")[0]
        lines.append(f"  {pascal_name}({params}) — {doc}")
    return "\n".join(lines)


def _dispatch(operation: str, group_name: str, params: dict):
    ops = _group_ops.get(group_name, {})
    fn = ops.get(operation)
    if fn is None:
        available = ", ".join(sorted(ops.keys()))
        raise ValueError(f"Unknown operation: {operation}. Available: {available}")
    return _coerce_call(fn, params)


def _register_tools():
    groups: dict[str, tuple] = {}

    for _importer, modname, _ispkg in pkgutil.walk_packages(_tools_pkg.__path__, _tools_pkg.__name__ + "."):
        module = __import__(modname, fromlist=[""])
        for attr_name, fn in inspect.getmembers(module, inspect.isfunction):
            if not hasattr(fn, "_mcp_group"):
                continue
            group = fn._mcp_group
            if group is ROOT:
                mcp.tool()(fn)
            else:
                if group.name not in groups:
                    groups[group.name] = (group, {})
                groups[group.name][1][attr_name] = fn

    for group_name, (group, fns) in groups.items():
        ops = {_to_pascal(n): fn for n, fn in fns.items()}
        _group_ops[group_name] = ops
        for pascal_name in ops:
            _all_grouped[pascal_name] = group_name

        def _make_tool(gname, gdoc):
            def tool_fn(operation: str, params: dict = {}):
                if operation == "help":
                    return _build_help(gname)
                return _dispatch(operation, gname, params)
            tool_fn.__name__ = gname
            tool_fn.__qualname__ = gname
            tool_fn.__doc__ = gdoc
            return tool_fn

        mcp.tool()(_make_tool(group_name, group.doc))


_register_tools()
