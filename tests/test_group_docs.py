"""Group doc examples must name operations their group actually exposes.

An example naming a non-existent operation makes an agent's first call fail,
and nothing but the registration-time rendering catches the drift.
"""

from __future__ import annotations

import inspect

import pytest

from incus_mcp import server
from incus_mcp.registry import Group
from incus_mcp.tools import groups


def test_group_docs_resolve_operation_placeholders():
    declared = [
        obj
        for _, obj in inspect.getmembers(groups, lambda o: isinstance(o, Group))
        if obj.name in server._group_ops
    ]
    assert len(declared) == len(server._group_ops)
    for group in declared:
        rendered = server._render_group_doc(
            group.name, group.doc, server._group_ops[group.name]
        )
        assert "$" not in rendered, (
            f"{group.name} doc left a placeholder unrendered"
        )


def test_render_group_doc_rejects_unknown_placeholder():
    with pytest.raises(RuntimeError, match="NoSuchOp"):
        server._render_group_doc(
            "incus_read",
            'Example: incus_read(operation="$NoSuchOp")',
            {"ListInstances": None},
        )


def test_render_group_doc_rejects_hardcoded_operation():
    with pytest.raises(RuntimeError, match="hardcodes"):
        server._render_group_doc(
            "incus_read",
            'Example: incus_read(operation="ListInstances")',
            {"ListInstances": None},
        )

    with pytest.raises(RuntimeError, match="hardcodes"):
        server._render_group_doc(
            "incus_read",
            'Example: incus_read(operation = "ListInstances")',
            {"ListInstances": None},
        )


def test_render_group_doc_resolves_meta_and_keeps_generic_form():
    rendered = server._render_group_doc(
        "incus_read",
        'operation="$help" or operation="$schema" or operation="<OpName>"',
        {},
    )
    assert rendered == (
        'operation="help" or operation="schema" or operation="<OpName>"'
    )
