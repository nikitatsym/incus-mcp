"""Step 5 fixtures: tools/read.py v2.5 annotations.

`_build_help` / `_build_schema` are exercised against the real registry -
no HTTP, no `stub_client` needed. The schema tests confirm `_UNSET` never
leaks into help output and that every migrated field carries its
Field(description=...) into the JSON Schema.
"""

from __future__ import annotations

import pytest

import incus_mcp.server as server


HELP = server._build_help("incus_read")


def test_help_lists_all_grouped_ops():
    assert "83 operations available" in HELP


def test_no_unset_leak_in_help():
    assert "_Unset" not in HELP
    assert "_UNSET" not in HELP


def test_list_instances_signature_and_bullets():
    assert (
        "ListInstances(project?: str | None, filter?: str | None, "
        "all_projects: bool = False)"
    ) in HELP
    assert "    project: Incus project (default project when omitted)." in HELP
    assert (
        "    filter: Incus API filter expression "
        "(e.g. 'status eq Running,type eq container')."
    ) in HELP
    assert "    all_projects: List across every project the caller can see." in HELP


def test_log_op_signature_and_bullets():
    assert (
        "GetInstanceLog(name: str, filename: str, "
        "tail: int = 100, filter?: str | None)"
    ) in HELP
    assert "    tail: Return last N lines (0 = full content)." in HELP
    assert "    filter: Regex applied line by line before tail." in HELP


def test_get_metrics_uses_zero_default():
    assert "GetMetrics(tail: int = 0, filter?: str | None)" in HELP


def test_list_volumes_type_bullet():
    assert (
        "ListVolumes(pool: str, project?: str | None, type?: str | None)"
    ) in HELP
    assert (
        "    type: Filter by volume type "
        "(custom, container, image, virtual-machine)."
    ) in HELP


def test_get_console_output_project_and_regex_filter():
    # get_console_output has both `project` (Incus project) AND
    # `filter` (regex, not the API filter). Two bullets under the same op.
    assert (
        "GetConsoleOutput(name: str, project?: str | None, "
        "tail: int = 100, filter?: str | None)"
    ) in HELP


def test_search_finds_log_ops():
    out = server._build_help("incus_read", search="log")
    for op in ("ListInstanceLogs", "GetInstanceLog", "GetNetworkAclLog"):
        assert op in out


def test_search_no_local_hits_reports_cleanly():
    out = server._build_help("incus_read", search="zzz-no-such-thing")
    assert "No ops in incus_read" in out


def test_schema_list_instances():
    schema = server._build_schema("incus_read", "ListInstances")
    assert schema["additionalProperties"] is False
    assert schema.get("required", []) == []
    props = schema["properties"]
    assert (
        props["project"]["description"]
        == "Incus project (default project when omitted)."
    )
    assert props["filter"]["description"].startswith("Incus API filter")
    assert (
        props["all_projects"]["description"]
        == "List across every project the caller can see."
    )


def test_schema_log_op_has_regex_description():
    schema = server._build_schema("incus_read", "GetInstanceLog")
    props = schema["properties"]
    assert props["tail"]["description"] == "Return last N lines (0 = full content)."
    assert props["filter"]["description"] == "Regex applied line by line before tail."


def test_schema_list_volumes_type_description():
    schema = server._build_schema("incus_read", "ListVolumes")
    assert (
        schema["properties"]["type"]["description"]
        == "Filter by volume type (custom, container, image, virtual-machine)."
    )


async def test_unknown_param_rejected():
    # Pydantic validation runs before the fn is called - no HTTP needed.
    with pytest.raises(ValueError, match="foo"):
        await server._dispatch(
            "ListInstances", "incus_read", {"foo": "bar"}
        )


async def test_missing_required_param():
    with pytest.raises(ValueError, match="name"):
        await server._dispatch("ShowInstance", "incus_read", {})
