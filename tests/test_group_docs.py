"""Group doc examples must name operations their group actually exposes.

An example naming a non-existent operation makes an agent's first call fail,
and nothing but the registration-time validator catches the drift.
"""

from __future__ import annotations

import inspect

import pytest

from incus_mcp import server
from incus_mcp.registry import Group
from incus_mcp.tools import groups


def test_group_doc_examples_name_registered_operations():
    declared = [
        obj
        for _, obj in inspect.getmembers(groups, lambda o: isinstance(o, Group))
        if obj.name in server._group_ops
    ]
    assert len(declared) == len(server._group_ops)
    for group in declared:
        for name in server._EXAMPLE_OPERATION.findall(group.doc):
            if name == "help":
                continue
            assert name in server._group_ops[group.name], (
                f"{group.name} example names {name!r}, which it does not expose"
            )


def test_doc_example_validation_rejects_unknown_operation():
    with pytest.raises(RuntimeError, match="NoSuchOp"):
        server._validate_doc_examples(
            "incus_read",
            'Example: incus_read(operation="NoSuchOp")',
            {"ListInstances": None},
        )

    server._validate_doc_examples("incus_read", 'operation="help"', {})
