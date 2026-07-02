"""Incus MCP server - auto-discovery, Pydantic validation, schema introspection, dispatch."""

from __future__ import annotations

import inspect
import pkgutil
import types
import typing
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    create_model,
    field_validator,
)

from . import tools as _tools_pkg
from .registry import ROOT, _UNSET, _Unset

mcp = FastMCP("incus")

_group_ops: dict[str, dict[str, Callable[..., Any]]] = {}
_all_grouped: dict[str, str] = {}


def _to_pascal(name: str) -> str:
    """list_instances -> ListInstances"""
    return "".join(w.capitalize() for w in name.split("_"))


def _build_params_model(fn: Callable[..., Any]) -> type[BaseModel]:
    """Build a Pydantic model from a function's signature.

    - Parameters without a default become required fields.
    - `Annotated[T, Field(description=..., ...)]` metadata flows into the
      generated JSON Schema.
    - `extra='forbid'` - unknown keys are rejected at validation time.
    - Loose string->bool coercion is applied to bool-typed fields before
      validation, so MCP clients that pass JSON-string booleans don't trip
      Pydantic's strict bool parser.
    """
    hints = typing.get_type_hints(fn, include_extras=True)
    sig = inspect.signature(fn)
    fields: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if param.kind is inspect.Parameter.VAR_KEYWORD:
            raise RuntimeError(
                f"Tool function {fn.__name__!r} declares **{name}; "
                "Incus tools must have explicit parameters only."
            )
        ann = hints.get(name, Any)
        if param.default is inspect.Parameter.empty:
            fields[name] = (ann, ...)
        elif isinstance(param.default, _Unset):
            # default_factory so `model_dump(exclude_unset=True)` in
            # `_coerce_call` keeps the caller's "omitted" state distinct
            # from an explicit None all the way to the body builders.
            fields[name] = (ann, Field(default_factory=lambda: _UNSET))
        else:
            fields[name] = (ann, param.default)

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_string_bool(cls, v: Any, info: Any) -> Any:
        if not isinstance(v, str):
            return v
        ann = cls.model_fields[info.field_name].annotation
        if bool not in (ann,) + typing.get_args(ann):
            return v
        lower = v.lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False
        return v

    return create_model(
        f"{_to_pascal(fn.__name__)}Params",
        __config__=ConfigDict(extra="forbid"),
        __validators__={"_coerce_string_bool": _coerce_string_bool},
        **fields,
    )


def _prepare_op(fn: Callable[..., Any]) -> None:
    """Cache the params model and parsed docstring on the function."""
    fn._mcp_params_model = _build_params_model(fn)  # type: ignore[attr-defined]
    doc = inspect.getdoc(fn) or ""
    head, _, body = doc.partition("\n\n")
    fn._mcp_doc_head = " ".join(head.split())  # type: ignore[attr-defined]
    fn._mcp_doc_body = body.rstrip()  # type: ignore[attr-defined]


def _format_validation_error(
    exc: ValidationError, op_name: str, group_name: str
) -> str:
    """Pydantic ValidationError -> readable multi-line message."""
    lines = [f"Invalid params for {op_name}:"]
    for e in exc.errors():
        loc = ".".join(str(x) for x in e["loc"]) or "<root>"
        got = repr(e.get("input"))
        if len(got) > 80:
            got = got[:77] + "..."
        lines.append(f"  - {loc}: {e['msg']} (got {got})")
    lines.append(
        f"Call {group_name}(operation='schema', params={{\"op\": \"{op_name}\"}}) "
        "for the full parameter spec."
    )
    return "\n".join(lines)


def _coerce_call(fn: Callable[..., Any], params: dict[str, Any]) -> Any:
    """Validate params via the function's Pydantic model, then call fn.

    Field-level type mismatches, missing required fields, and unknown keys
    all raise ValueError pointing at the offending field. Omitted
    `_UNSET`-defaulted keys never reach fn (`exclude_unset=True`). Async
    functions return their coroutine as-is - `_dispatch` awaits it.
    """
    model: type[BaseModel] = fn._mcp_params_model  # type: ignore[attr-defined]
    try:
        validated = model.model_validate(params)
    except ValidationError as e:
        op_name = _to_pascal(fn.__name__)
        group_name = fn._mcp_group.name  # type: ignore[attr-defined]
        raise ValueError(_format_validation_error(e, op_name, group_name)) from e
    return fn(**validated.model_dump(exclude_unset=True))


def _type_to_str(hint: Any) -> str:
    """Compact human-readable rendering of a type hint for help text.

    Unions keep `None` visible (`str | None`) - nullability is part of the
    caller-facing contract. `_Unset` never renders: it's an internal
    default sentinel, not part of any parameter's type.
    """
    if hint is type(None):
        return "None"
    if hint is Any:
        return "any"
    origin = typing.get_origin(hint)
    args = typing.get_args(hint)
    if origin is typing.Literal:
        return f"Literal[{', '.join(repr(a) for a in args)}]"
    if origin is typing.Union or isinstance(hint, types.UnionType):
        parts = [_type_to_str(a) for a in args if a is not _Unset]
        return " | ".join(parts) or "any"
    if origin is list:
        return f"list[{_type_to_str(args[0])}]" if args else "list"
    if origin is dict:
        if len(args) == 2:
            return f"dict[{_type_to_str(args[0])}, {_type_to_str(args[1])}]"
        return "dict"
    if origin is tuple:
        return f"tuple[{', '.join(_type_to_str(a) for a in args)}]" if args else "tuple"
    if hasattr(hint, "__name__"):
        return str(hint.__name__)
    return str(hint).replace("typing.", "")


def _format_param_for_help(name: str, hint: Any, default: Any) -> str:
    """Render one parameter: `name: T` (required), `name?: T` (_UNSET
    default, may be omitted), or `name: T = default` (real default)."""
    type_str = _type_to_str(hint)
    if default is inspect.Parameter.empty:
        return f"{name}: {type_str}"
    if isinstance(default, _Unset):
        return f"{name}?: {type_str}"
    return f"{name}: {type_str} = {default!r}"


def _render_ops_block(ops: dict[str, Callable[..., Any]]) -> str:
    """Per-op signature line with docstring head, body indented four spaces,
    then a `name: description` bullet for every param with a Field
    description."""
    lines: list[str] = []
    for pascal_name, fn in sorted(ops.items()):
        hints = typing.get_type_hints(fn, include_extras=False)
        sig = inspect.signature(fn)
        parts = [
            _format_param_for_help(n, hints.get(n, Any), p.default)
            for n, p in sig.parameters.items()
        ]
        lines.append(f"  {pascal_name}({', '.join(parts)}) - {fn._mcp_doc_head}")  # type: ignore[attr-defined]
        for body_line in fn._mcp_doc_body.splitlines():  # type: ignore[attr-defined]
            lines.append(f"    {body_line}" if body_line else "")
        model: type[BaseModel] = fn._mcp_params_model  # type: ignore[attr-defined]
        for field_name, field in model.model_fields.items():
            if field.description:
                lines.append(f"    {field_name}: {field.description}")
    return "\n".join(lines)


def _build_help(group_name: str, search: str | None = None) -> str:
    """Per-op signatures with types and description bullets.

    Without `search`: every op in the group. With `search='foo'`: ops whose
    name or docstring contains `foo` (case-insensitive); when the local
    match set is empty but other groups match, a cross-group hint is
    appended so the agent learns where to look.
    """
    ops = _group_ops[group_name]
    header_suffix = (
        " Call operation='schema', params={'op': 'OpName'} for the full JSON Schema."
    )

    if search:
        s = search.lower()

        def _hit(pascal_name: str, fn: Callable[..., Any]) -> bool:
            return (
                s in pascal_name.lower()
                or s in fn.__name__.lower()
                or s in (inspect.getdoc(fn) or "").lower()
            )

        matched = {pn: fn for pn, fn in ops.items() if _hit(pn, fn)}
        elsewhere: dict[str, list[str]] = {}
        for op_name, other_group in _all_grouped.items():
            if other_group == group_name:
                continue
            if _hit(op_name, _group_ops[other_group][op_name]):
                elsewhere.setdefault(other_group, []).append(op_name)
        if not matched:
            msg = f"No ops in {group_name} matching {search!r}."
            if elsewhere:
                msg += " Found in other groups: " + "; ".join(
                    f"{g}: {', '.join(sorted(names))}"
                    for g, names in sorted(elsewhere.items())
                )
            else:
                msg += " Call operation='help' (no params) to list all ops."
            return msg
        header = (
            f"{len(matched)} of {len(ops)} operations in {group_name} "
            f"matching {search!r}.{header_suffix}"
        )
        body = _render_ops_block(matched)
        if elsewhere:
            body += "\n\nAlso matching in other groups: " + "; ".join(
                f"{g}: {', '.join(sorted(names))}"
                for g, names in sorted(elsewhere.items())
            )
        return f"{header}\n{body}"

    header = f"{len(ops)} operations available.{header_suffix}"
    return f"{header}\n{_render_ops_block(ops)}"


def _build_schema(group_name: str, op: str | None = None) -> dict[str, Any] | list[str]:
    """JSON Schema for one op, or the sorted list of op names when op is None."""
    ops = _group_ops[group_name]
    if op is None:
        return sorted(ops.keys())
    if op not in ops:
        raise ValueError(
            f"Unknown operation {op!r} in {group_name}. Available: {sorted(ops)}"
        )
    fn = ops[op]
    model: type[BaseModel] = fn._mcp_params_model  # type: ignore[attr-defined]
    schema: dict[str, Any] = model.model_json_schema()
    doc = inspect.getdoc(fn) or ""
    if doc:
        schema["description"] = doc
    return schema


async def _dispatch(operation: str, group_name: str, params: dict[str, Any]) -> Any:
    """Route help / schema / op-name; fail loud on anything wrong.

    Errors propagate as ValueError / APIError - no `{"error": ...}`
    wrapping. Async ops (Step 8 waiters) are awaited here; sync ops keep
    the direct-call path.
    """
    if operation == "help":
        return _build_help(group_name, search=params.get("search"))
    if operation == "schema":
        return _build_schema(group_name, params.get("op"))
    ops = _group_ops[group_name]
    fn = ops.get(operation)
    if fn is None:
        if operation in _all_grouped:
            correct = _all_grouped[operation]
            raise ValueError(
                f"{operation!r} belongs to {correct!r}, not {group_name!r}. "
                f"Call {correct}(operation={operation!r}, ...) instead."
            )
        raise ValueError(
            f"Unknown operation {operation!r} in {group_name}. "
            f"Available: {', '.join(sorted(ops))}"
        )
    result = _coerce_call(fn, params)
    if inspect.iscoroutine(result):
        result = await result
    return result


def _make_tool(group_name: str, group_doc: str) -> Callable[..., Any]:
    async def tool_fn(operation: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        return await _dispatch(operation, group_name, params)

    tool_fn.__name__ = group_name
    tool_fn.__qualname__ = group_name
    tool_fn.__doc__ = group_doc
    return tool_fn


def _register_tools() -> None:
    """Discover @_op-decorated functions, build Pydantic models, register MCP tools."""
    groups: dict[str, tuple[Any, dict[str, Callable[..., Any]]]] = {}

    for _importer, modname, _ispkg in pkgutil.walk_packages(
        _tools_pkg.__path__, _tools_pkg.__name__ + "."
    ):
        module = __import__(modname, fromlist=[""])
        for attr_name, fn in inspect.getmembers(module, inspect.isfunction):
            if not hasattr(fn, "_mcp_group"):
                continue
            group = fn._mcp_group
            if group is ROOT:
                mcp.tool()(fn)
            else:
                _prepare_op(fn)
                if group.name not in groups:
                    groups[group.name] = (group, {})
                groups[group.name][1][attr_name] = fn

    for group_name, (group, fns) in groups.items():
        ops = {_to_pascal(n): fn for n, fn in fns.items()}
        _group_ops[group_name] = ops
        for pascal_name in ops:
            _all_grouped[pascal_name] = group_name

        mcp.tool()(_make_tool(group_name, group.doc))


_register_tools()
