"""Conformance check: every hand-written API call matches Incus's swagger spec.

Incus, like any Go service decoding into structs, drops query params and JSON
body fields it does not know instead of rejecting them, so a misspelled name is
an invisible bug: the call still returns 200 and the filter or field simply
never applies. Neither the type system nor the e2e smokes can see that class of
typo, so this test reads every registered op in `incus_mcp.tools` off its own
AST and asserts each call's method, path, query-param names and body-field
names against the pinned upstream spec.

The spec is vendored under `tests/data/` because no running Incus serves it -
it lives in the source tree as `doc/rest-api.yaml`. `scripts/fetch-incus-spec.py`
regenerates it from a git tag; `x-source` in the file records which one.
"""

from __future__ import annotations

import ast
import functools
import importlib
import inspect
import json
import pkgutil
import re
import sys
import textwrap
import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal, NamedTuple, TypeGuard

import pytest

from incus_mcp import server
from incus_mcp import tools as _tools_pkg
from incus_mcp.registry import ROOT


class _Waiver(NamedTuple):
    """`reason` is load-bearing: it must equal the block the extractor reports.

    A blocked op has all of its calls dropped, so waiving one by name alone
    would also waive whatever a later edit breaks in the same op. Matching the
    exact reason means a second, different block surfaces as a new finding.
    """

    reason: str
    why: str


# Ops whose call shape the extractor below cannot read. ONLY code shapes belong
# here - never a name mismatch, which is the whole point of this test.
UNANALYZABLE_OK: dict[str, _Waiver] = {
    "incus_version": _Waiver(
        "unknown client method 'check'",
        "calls the client's pathless startup probe; its GET /1.0 is the same "
        "endpoint get_server checks",
    ),
    "list_volumes": _Waiver(
        "path is a Name, not a literal",
        "path is assembled conditionally into a local variable; both variants "
        "(/1.0/storage-pools/{pool}/volumes[/{type}]) hand-checked against the spec",
    ),
    "operation_wait_start": _Waiver(
        "calls _run_drain(), which makes HTTP calls this extractor cannot read",
        "probes through asyncio.to_thread and hands the rest to the _poll / "
        "_run_drain helpers; its GET /1.0/operations/{id} is the same endpoint "
        "show_operation checks",
    ),
    "wait_operation": _Waiver(
        "path is a Name, not a literal",
        "replays a target path handed over by the pending-verify registry; those "
        "paths are checked where they are registered, and GET "
        "/1.0/operations/{id}/wait is hand-checked against the spec",
    ),
}

# Ops with no wire call of their own: they only drive the local wait registry,
# whose polling happens in operation_wait_start's background task.
NO_WIRE_CALL_OK: frozenset[str] = frozenset({
    "operation_wait_cancel",
    "operation_wait_poll",
    "waits_list",
})

# Ops whose endpoint is deliberately absent from the pinned spec. Reviewed
# entries only; the conformance test fails if the endpoint reappears.
SPEC_GAPS: dict[str, str] = {}

_SPEC_PATH = Path(__file__).parent / "data" / "incus-rest-api.json"

# Client verb -> HTTP method. `get_raw` is a GET that skips envelope decoding.
_CLIENT_VERBS = {
    "get": "GET",
    "get_raw": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
}
# `_qp` keyword -> wire name. Everything else is sent under its own keyword.
_QP_WIRE = {"all_projects": "all-projects"}
# Query names a spec path key may document by carrying them in its own query
# string. `recursion` is named nowhere else. `?public` is deliberately absent:
# it disambiguates the untrusted-client operation id (the endpoint carries
# `AllowUntrusted: true`), and no v7.3.0 handler reads a `public` query param.
_PROMOTED_KEY_PARAMS = frozenset({"recursion"})
# Kwargs that carry no name-bearing payload, and ones whose payload is raw
# bytes rather than a JSON object.
_NO_PAYLOAD_KWARGS = frozenset({"headers"})
_RAW_BODY_KWARGS = frozenset({"content"})

_PLACEHOLDER_SEGMENT = re.compile(r"^\{\w+\}$")
# A helper that reaches this marker makes calls the extractor cannot read.
_WIRE_MARKER = re.compile(r"_get_client\(\)\.|httpx\.")

# A dict whose keys the caller owns, so they cannot be read off the source.
_OPAQUE: None = None


class _Body(Enum):
    """A body whose field names are not readable, and why they are not.

    The two are not interchangeable against the spec: an endpoint documenting
    a raw upload wants bytes, one documenting a schema wants that object.
    """

    RAW = "raw bytes"
    CALLER_SUPPLIED = "a caller-supplied dict"


@functools.cache
def _hits_wire(target: Callable[..., Any]) -> bool:
    # getsource failing here is a loud test error by design: an unreadable
    # helper cannot be assumed clean.
    return bool(_WIRE_MARKER.search(inspect.getsource(target)))


@dataclass(frozen=True)
class _WireCall:
    """One outbound HTTP call, as read off the source of an op."""

    method: str
    path: str
    query: frozenset[str]
    body: frozenset[str] | _Body
    # Wire name -> the string values this call can send under it, where they
    # are statically known.
    query_values: dict[str, frozenset[str]] = field(default_factory=dict)


# Stand-in for a call the extractor gave up on; dropped with the rest once the
# op is marked unreadable.
_UNREADABLE = _WireCall("", "", frozenset(), frozenset())

# Payload as read off the source: wire name -> statically known values for it
# (empty when the value is computed). `None` stands for a caller-supplied dict.
_Payload = dict[str, frozenset[str]]


def _is_named(node: ast.expr | None, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_call_to(node: ast.AST | None, name: str) -> TypeGuard[ast.Call]:
    return isinstance(node, ast.Call) and _is_named(node.func, name)


def _merge(into: _Payload, other: _Payload) -> _Payload:
    for name, values in other.items():
        into[name] = into.get(name, frozenset()) | values
    return into


# -- AST extraction ---------------------------------------------------------


class _OpExtractor:
    """Reads the wire calls an op makes straight off its source.

    Every shape outside the grammar records a reason in `blocked` and the op is
    reported as unanalyzable rather than half-checked.
    """

    def __init__(self, fn: Callable[..., Any]) -> None:
        self.module = sys.modules[fn.__module__]
        self.params = list(inspect.signature(fn).parameters)
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        self.stmts: list[ast.stmt] = tree.body[0].body  # type: ignore[attr-defined]
        self.blocked: str | None = None

    def calls(self) -> list[_WireCall]:
        found = []
        called_attrs: set[int] = set()
        client_attrs: list[ast.Attribute] = []
        for node in self._walk():
            if isinstance(node, ast.Attribute) and _is_call_to(node.value, "_get_client"):
                client_attrs.append(node)
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if isinstance(fn, ast.Attribute) and _is_call_to(fn.value, "_get_client"):
                called_attrs.add(id(fn))
                found.append(self._from_client(node, fn.attr))
            elif isinstance(fn, ast.Attribute) and _is_named(fn.value, "httpx"):
                # The wire marker only guards helpers; an op reaching for httpx
                # itself would otherwise be read as making no call at all.
                self._block(f"calls httpx.{fn.attr}() directly, bypassing the client")
            elif _is_named(fn, "_register_pending_verify"):
                found.append(self._from_verify_target(node))
            elif isinstance(fn, ast.Name):
                self._check_helper(fn.id)
        for attr in client_attrs:
            if id(attr) not in called_attrs:
                self._block(f"client method {attr.attr!r} is passed around, not called here")
        return [] if self.blocked else found

    def _check_helper(self, name: str) -> None:
        """Block ops whose helpers hit the wire where this test cannot see."""
        target = getattr(self.module, name, None)
        # Registered ops another op drives are checked in their own right.
        if not inspect.isfunction(target) or hasattr(target, "_mcp_group"):
            return
        if _hits_wire(target):
            self._block(f"calls {name}(), which makes HTTP calls this extractor cannot read")

    def _walk(self) -> Iterator[ast.AST]:
        for stmt in self.stmts:
            yield from ast.walk(stmt)

    def _block(self, reason: str) -> None:
        if self.blocked is None:
            self.blocked = reason

    # -- literals -----------------------------------------------------------

    def _const_str(self, node: ast.expr | None) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        self._block(f"expected a string literal, found {type(node).__name__}")
        return ""

    def _values(self, node: ast.expr) -> frozenset[str]:
        """The string values an argument can carry, empty when computed."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return frozenset({node.value})
        return frozenset()

    # -- payloads -----------------------------------------------------------

    def _payload(self, value: ast.expr | None) -> _Payload | None:
        if value is None or (isinstance(value, ast.Constant) and value.value is None):
            return {}
        if isinstance(value, ast.Dict):
            return self._dict_payload(value)
        if _is_call_to(value, "_qp"):
            return self._qp_payload(value)
        if isinstance(value, ast.Name):
            return self._resolve_var(value.id)
        self._block(f"payload is a {type(value).__name__}, not a readable dict")
        return {}

    def _dict_payload(self, node: ast.Dict) -> _Payload:
        if any(key is None for key in node.keys):
            self._block("dict literal uses ** unpacking")
            return {}
        return {
            self._const_str(key): self._values(value)
            for key, value in zip(node.keys, node.values)
        }

    def _qp_payload(self, node: ast.Call) -> _Payload:
        if node.args:
            self._block("_qp() is called positionally")
            return {}
        payload: _Payload = {}
        for kw in node.keywords:
            if kw.arg is None:
                self._block("_qp() is called with ** unpacking")
                return {}
            payload[_QP_WIRE.get(kw.arg, kw.arg)] = self._values(kw.value)
        return payload

    def _resolve_var(self, name: str) -> _Payload | None:
        """Merge everything a local dict variable can end up carrying."""
        payload: _Payload = {}
        assigned = False
        for node in self._walk():
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(node, ast.Assign):
                targets, value = list(node.targets), node.value
            elif isinstance(node, ast.AnnAssign):
                targets, value = [node.target], node.value
            elif isinstance(node, ast.AugAssign) and _is_named(node.target, name):
                self._block(f"augmented assignment to {name!r}")
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and _is_named(node.func.value, name)
            ):
                self._block(f"{name}.{node.func.attr}() mutates the payload")
            # An alias can be mutated where the tracked name never appears.
            if targets and _is_named(value, name):
                self._block(f"{name!r} is aliased to another local")
            for target in targets:
                if _is_named(target, name):
                    initial = self._payload(value)
                    if initial is None:
                        return _OPAQUE
                    _merge(payload, initial)
                    assigned = True
                elif isinstance(target, ast.Subscript) and _is_named(target.value, name):
                    _merge(payload, {self._const_str(target.slice): self._values(value)})
        if assigned:
            return payload
        if name in self.params:
            return _OPAQUE  # the caller supplies the object; its keys are its own
        self._block(f"no assignment to {name!r} found in the op")
        return {}

    # -- call shapes --------------------------------------------------------

    def _from_client(self, node: ast.Call, verb: str) -> _WireCall:
        if verb not in _CLIENT_VERBS:
            self._block(f"unknown client method {verb!r}")
            return _UNREADABLE
        if not node.args:
            self._block(f"{verb}() called without a path")
            return _UNREADABLE
        path = self._path(node.args[0])
        if node.args[1:]:
            self._block(f"{verb}() passes a payload positionally")
            return _UNREADABLE
        query: _Payload = {}
        body: frozenset[str] | _Body = frozenset()
        for kw in node.keywords:
            if kw.arg == "params":
                names = self._payload(kw.value)
                if names is None:
                    self._block(f"{verb}() is handed an opaque param dict")
                else:
                    _merge(query, names)
            elif kw.arg == "json":
                fields = self._payload(kw.value)
                body = _Body.CALLER_SUPPLIED if fields is None else frozenset(fields)
            elif kw.arg in _RAW_BODY_KWARGS:
                body = _Body.RAW
            elif kw.arg not in _NO_PAYLOAD_KWARGS:
                self._block(f"{verb}() carries a payload in {kw.arg!r}")
        return _WireCall(
            _CLIENT_VERBS[verb],
            path,
            frozenset(query),
            body,
            {name: values for name, values in query.items() if values},
        )

    def _from_verify_target(self, node: ast.Call) -> _WireCall:
        """The GET a waiter replays later to confirm an async write landed."""
        if len(node.args) != 4:
            self._block("_register_pending_verify() is not shaped (result, sent, path, params)")
            return _UNREADABLE
        query = self._payload(node.args[3])
        if query is None:
            self._block("_register_pending_verify() is handed an opaque param dict")
            return _UNREADABLE
        return _WireCall("GET", self._path(node.args[2]), frozenset(query), frozenset())

    def _path(self, node: ast.expr) -> str:
        if isinstance(node, ast.Constant):
            return self._const_str(node)
        if not isinstance(node, ast.JoinedStr):
            self._block(f"path is a {type(node).__name__}, not a literal")
            return ""
        parts = []
        for piece in node.values:
            if isinstance(piece, ast.Constant):
                parts.append(str(piece.value))
            elif isinstance(piece, ast.FormattedValue) and isinstance(piece.value, ast.Name):
                parts.append("{" + piece.value.id + "}")
            else:
                self._block("path f-string interpolates an expression")
                return ""
        return "".join(parts)


@dataclass(frozen=True)
class _Ops:
    analyzed: dict[str, list[_WireCall]]
    unanalyzable: dict[str, str]
    no_wire_call: list[str]


@functools.lru_cache(maxsize=1)
def _discovered() -> tuple[dict[str, Callable[..., Any]], dict[str, list[str]]]:
    """Every @_op-decorated function, discovered the way the server does.

    Returns the ops by name plus the names defined in more than one module:
    ops are swept by function name, so a collision would drop one of them from
    the sweep instead of failing anything.
    """
    by_name: dict[str, list[tuple[str, Callable[..., Any]]]] = {}
    for _importer, modname, _ispkg in pkgutil.walk_packages(
        _tools_pkg.__path__, _tools_pkg.__name__ + "."
    ):
        module = importlib.import_module(modname)
        for name, fn in inspect.getmembers(module, inspect.isfunction):
            if hasattr(fn, "_mcp_group") and fn.__module__ == modname:
                by_name.setdefault(name, []).append((modname, fn))
    return (
        {name: entries[0][1] for name, entries in by_name.items()},
        {
            name: [modname for modname, _ in entries]
            for name, entries in by_name.items()
            if len(entries) > 1
        },
    )


def _registered_ops() -> dict[str, Callable[..., Any]]:
    return _discovered()[0]


@functools.lru_cache(maxsize=1)
def _extract_ops() -> _Ops:
    analyzed: dict[str, list[_WireCall]] = {}
    unanalyzable: dict[str, str] = {}
    no_wire_call: list[str] = []
    for name, fn in sorted(_registered_ops().items()):
        extractor = _OpExtractor(fn)
        calls = extractor.calls()
        if extractor.blocked:
            unanalyzable[name] = extractor.blocked
        elif calls:
            analyzed[name] = calls
        else:
            no_wire_call.append(name)  # wait-registry machinery, no wire call
    return _Ops(analyzed, unanalyzable, no_wire_call)


# -- Spec index -------------------------------------------------------------


def _segments(path: str) -> list[str | None]:
    """Split into /-segments; placeholder segments become None."""
    return [
        None if _PLACEHOLDER_SEGMENT.match(seg) else seg
        for seg in path.strip("/").split("/")
    ]


def _matches(ours: list[str | None], spec: list[str | None]) -> bool:
    """A spec placeholder accepts anything; our placeholder needs one."""
    if len(ours) != len(spec):
        return False
    return all(
        spec_seg is None or our_seg == spec_seg for our_seg, spec_seg in zip(ours, spec)
    )


@dataclass
class _Endpoint:
    """Accumulator for one path+method, merged across the spec's key variants."""

    query: set[str] = field(default_factory=set)
    query_enums: dict[str, frozenset[str]] = field(default_factory=dict)
    body: set[str] = field(default_factory=set)
    # A body parameter with no schema is a raw upload: its field names are not
    # the spec's business, so the body check stands down unless some variant
    # of the endpoint does declare a schema.
    body_declared: bool = False
    body_schema: bool = False


class _Spec:
    """Query/body name sets per (path template, method), matched structurally.

    Incus documents recursion variants as separate path keys carrying a query
    string (`/1.0/instances?recursion=1`), so keys are split on `?` and merged.
    Only `_PROMOTED_KEY_PARAMS` are read out of the key itself; every other
    name has to appear in an operation's `parameters` list to count.
    """

    def __init__(self, doc: dict[str, Any]) -> None:
        self._defs: dict[str, Any] = doc.get("definitions") or {}
        self.source: dict[str, str] = doc.get("x-source") or {}
        merged: dict[tuple[str, str], _Endpoint] = {}
        for key, item in doc["paths"].items():
            path, _, query = key.partition("?")
            promoted = {
                part.partition("=")[0] for part in query.split("&") if part
            } & _PROMOTED_KEY_PARAMS
            for method, operation in item.items():
                if not isinstance(operation, dict):
                    continue
                endpoint = merged.setdefault((path, method.upper()), _Endpoint())
                endpoint.query |= promoted
                self._read_parameters(operation, endpoint)
        self.endpoints = {
            key: (
                frozenset(endpoint.query),
                None if endpoint.body_declared and not endpoint.body_schema
                else frozenset(endpoint.body),
            )
            for key, endpoint in merged.items()
        }
        self.query_enums = {key: endpoint.query_enums for key, endpoint in merged.items()}
        self._templates = {path: _segments(path) for path, _ in merged}

    def _read_parameters(self, operation: dict[str, Any], endpoint: _Endpoint) -> None:
        for param in operation.get("parameters") or []:
            where = param.get("in")
            if where == "query":
                endpoint.query.add(param["name"])
                # Formal enums only; prose-documented value sets are not
                # machine-checkable and are skipped.
                values = param.get("enum") or (param.get("items") or {}).get("enum")
                if values:
                    endpoint.query_enums[param["name"]] = frozenset(values)
            elif where == "formData":
                endpoint.body.add(param["name"])
            elif where == "body":
                endpoint.body_declared = True
                schema = param.get("schema")
                if schema:
                    endpoint.body_schema = True
                    endpoint.body |= self._properties(schema)

    def _properties(self, schema: dict[str, Any], depth: int = 0) -> set[str]:
        if depth > 8 or not isinstance(schema, dict):
            return set()
        ref = schema.get("$ref")
        if ref:
            return self._properties(self._defs.get(ref.rsplit("/", 1)[-1]) or {}, depth + 1)
        names = set(schema.get("properties") or {})
        for member in schema.get("allOf") or []:
            names |= self._properties(member, depth + 1)
        return names

    def _pool(self, path: str) -> list[str]:
        # An exact template match is unambiguous by construction; structural
        # matching is the fallback for paths whose placeholders are named
        # differently ({pool} here, {poolName} in the spec).
        if path in self._templates:
            return [path]
        ours = _segments(path)
        pool = [p for p, template in self._templates.items() if _matches(ours, template)]
        # A spec placeholder swallows one of our literal segments, so keep only
        # the least-placeholder matches: `logs/exec-output` resolves to its own
        # template rather than to `logs/{filename}`.
        literals = {p: sum(seg is not None for seg in self._templates[p]) for p in pool}
        best = max(literals.values(), default=0)
        return [p for p in pool if literals[p] == best]

    def candidates(self, path: str, method: str) -> list[str]:
        return [p for p in self._pool(path) if (p, method) in self.endpoints]

    def describe_pool(self, path: str) -> str:
        known = sorted(
            f"{m} {p}" for p in self._pool(path) for (p2, m) in self.endpoints if p2 == p
        )
        return ", ".join(known) if known else "nothing with this path shape"


@pytest.fixture(scope="session")
def spec() -> _Spec:
    """The pinned upstream spec; no running Incus serves one to fetch."""
    return _Spec(json.loads(_SPEC_PATH.read_text()))


# -- Tests ------------------------------------------------------------------


def test_discovery_sweeps_every_op_the_server_exposes() -> None:
    ops, duplicates = _discovered()
    assert not duplicates, (
        "These op names are defined in more than one tool module, so only one "
        f"of each is swept - and the server exposes both: {duplicates}"
    )
    swept = {
        server._to_pascal(name) for name, fn in ops.items() if fn._mcp_group is not ROOT
    }
    exposed = {name for ops_by_name in server._group_ops.values() for name in ops_by_name}
    assert swept == exposed, "op discovery disagrees with the server's registry"
    extracted = _extract_ops()
    assert len(extracted.analyzed) + len(extracted.unanalyzable) + len(
        extracted.no_wire_call
    ) == len(ops)


def test_every_unanalyzable_op_is_allowlisted() -> None:
    unknown = {
        name: reason
        for name, reason in _extract_ops().unanalyzable.items()
        if name not in UNANALYZABLE_OK or UNANALYZABLE_OK[name].reason != reason
    }
    assert not unknown, (
        "Ops whose calls this test cannot read are missing from UNANALYZABLE_OK, "
        "or are blocked for a different reason than the one waived - a blocked "
        "op has ALL its calls dropped, so the waived reason has to be the one "
        "that fired. Reshape the op into a readable form, teach the extractor "
        "the shape, or waive it - code shapes only, NEVER a name mismatch:\n"
        + "\n".join(f"  {name}: {reason}" for name, reason in sorted(unknown.items()))
    )


def test_allowlist_has_no_stale_entries() -> None:
    stale = sorted(set(UNANALYZABLE_OK) - set(_extract_ops().unanalyzable))
    assert not stale, (
        "These ops are analyzable now - drop them from UNANALYZABLE_OK so the "
        f"allowlist can only shrink: {stale}"
    )
    orphaned = sorted(set(SPEC_GAPS) - set(_extract_ops().analyzed))
    assert not orphaned, f"SPEC_GAPS names ops with no analyzed wire call: {orphaned}"


def test_no_wire_call_ops_are_expected() -> None:
    ops = _extract_ops()
    unexpected = sorted(set(ops.no_wire_call) - NO_WIRE_CALL_OK)
    assert not unexpected, (
        "Ops with no readable wire call of their own. If they truly only drive "
        f"local state or other registered ops, add them to NO_WIRE_CALL_OK: {unexpected}"
    )
    stale = sorted(NO_WIRE_CALL_OK - set(ops.no_wire_call))
    assert not stale, f"NO_WIRE_CALL_OK entries no longer match reality: {stale}"


def _arg_wire_names(fn: Callable[..., Any]) -> dict[str, str]:
    """Best-effort map from a signature arg to the wire name it is sent under.

    Sources: `_qp()` keywords, dict literals `{"key": arg}`, and subscript
    assigns `body["key"] = arg`. Args sent under their own name need no entry;
    args whose value is transformed before sending stay unmapped and are simply
    not enum-checked.
    """
    mapping: dict[str, str] = {}
    for node in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(fn)))):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.targets[0].slice, ast.Constant)
            and isinstance(node.value, ast.Name)
        ):
            mapping[node.value.id] = node.targets[0].slice.value
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and isinstance(value, ast.Name):
                    mapping[value.id] = key.value
        elif _is_call_to(node, "_qp"):
            for kw in node.keywords:
                if kw.arg is not None and isinstance(kw.value, ast.Name):
                    mapping[kw.value.id] = _QP_WIRE.get(kw.arg, kw.arg)
    return mapping


def _literal_values(annotation: Any) -> frozenset[str]:
    """String values of every Literal reachable inside the annotation."""
    values: set[str] = set()
    stack = [annotation]
    while stack:
        ann = stack.pop()
        if typing.get_origin(ann) is Literal:
            values |= {a for a in typing.get_args(ann) if isinstance(a, str)}
        else:
            stack.extend(typing.get_args(ann))
    return frozenset(values)


def _sent_query_values(op: str, call: _WireCall) -> dict[str, frozenset[str]]:
    """Statically known values per query name: constants plus Literal domains."""
    sent = dict(call.query_values)
    fn = _registered_ops()[op]
    wire_of = _arg_wire_names(fn)
    for arg, annotation in typing.get_type_hints(fn, include_extras=True).items():
        values = _literal_values(annotation)
        wire = wire_of.get(arg, arg)
        if values and wire in call.query:
            sent[wire] = sent.get(wire, frozenset()) | values
    return sent


def test_query_values_match_spec_enums(spec: _Spec) -> None:
    """A value the spec's enum lacks is the silent-lie class again: Incus falls
    back to its default instead of erroring. Query params only - the spec
    declares no enum on any body field."""
    findings: list[str] = []
    for op, calls in sorted(_extract_ops().analyzed.items()):
        if op in SPEC_GAPS:
            continue
        for call in calls:
            matches = spec.candidates(call.path, call.method)
            if len(matches) != 1:
                continue
            enums = spec.query_enums.get((matches[0], call.method), {})
            if not enums:
                continue
            for wire, values in _sent_query_values(op, call).items():
                extra = sorted(values - enums[wire]) if wire in enums else []
                if extra:
                    findings.append(
                        f"{op} -> {call.method} {call.path} ?{wire}: values {extra} "
                        f"are not in the spec enum {sorted(enums[wire])}"
                    )
    assert not findings, (
        f"{len(findings)} query value(s) the spec enum lacks; Incus silently "
        "substitutes its default for these:\n" + "\n".join(f"  {f}" for f in findings)
    )


def _body_finding(ours: frozenset[str] | _Body, allowed: frozenset[str] | None) -> str:
    """Compare the body we send against the one the spec's body param declares.

    `allowed is None` marks an endpoint whose body parameter carries no schema
    - a raw upload. Feeding one a JSON object, or handing bytes to an endpoint
    that documents a schema, is a wire mismatch even when no field name is
    readable on our side.
    """
    if ours is _Body.RAW:
        if allowed is None:
            return ""
        return "sends a raw body where the spec declares a JSON schema"
    if allowed is None:
        if ours is _Body.CALLER_SUPPLIED or ours:
            return "sends a JSON body where the spec declares a raw upload"
        return ""
    if ours is _Body.CALLER_SUPPLIED:
        return ""  # the caller owns the keys; there is nothing to compare
    bad = sorted(ours - allowed)
    if not bad:
        return ""
    return f"body fields {bad} are not in the spec; it accepts {sorted(allowed)}"


def test_wire_calls_match_spec(spec: _Spec) -> None:
    findings: list[str] = []
    for op, calls in sorted(_extract_ops().analyzed.items()):
        for call in calls:
            where = f"{op}: {call.method} {call.path}"
            matches = spec.candidates(call.path, call.method)
            if op in SPEC_GAPS:
                if matches:
                    findings.append(
                        f"{where}: endpoint is back in the spec - drop it from SPEC_GAPS"
                    )
                continue
            if not matches:
                findings.append(
                    f"{where}: no such endpoint in the spec; it has "
                    f"{spec.describe_pool(call.path)}"
                )
                continue
            if len(matches) > 1:
                findings.append(f"{where}: ambiguous, matches spec paths {matches}")
                continue
            allowed_query, allowed_body = spec.endpoints[matches[0], call.method]
            bad_query = sorted(call.query - allowed_query)
            if bad_query:
                findings.append(
                    f"{where}: query params {bad_query} are not in the spec; "
                    f"it accepts {sorted(allowed_query)}"
                )
            bad_body = _body_finding(call.body, allowed_body)
            if bad_body:
                findings.append(f"{where}: {bad_body}")
    assert not findings, (
        f"{len(findings)} call(s) disagree with the Incus spec "
        f"({spec.source.get('tag', 'unpinned')}). Incus drops unknown names "
        "silently, so each of these is a request that quietly does not do what "
        "it says:\n" + "\n".join(f"  {f}" for f in findings)
    )
