"""Step 7 fixtures: tools/execute.py v2.5 annotations.

`Literal[...]` on `bulk_instance_state.action` renders in `_build_help` /
JSON Schema. `_UNSET`-defaulted project renders with `?`. Field bullets
land under each op that carries a description.
"""

from __future__ import annotations

import incus_mcp.server as server


HELP = server._build_help("incus_execute")


def test_no_unset_leak_in_help():
    assert "_Unset" not in HELP
    assert "_UNSET" not in HELP


def test_start_instance_signature():
    assert "StartInstance(name: str, project?: str | None)" in HELP


def test_stop_instance_has_force_bullet():
    assert (
        "StopInstance(name: str, project?: str | None, force: bool = False)"
    ) in HELP
    assert "    force: Immediate kill instead of graceful shutdown." in HELP


def test_restart_instance_has_force_bullet():
    assert (
        "RestartInstance(name: str, project?: str | None, force: bool = False)"
    ) in HELP


def test_freeze_and_unfreeze_lack_force():
    assert "FreezeInstance(name: str, project?: str | None)" in HELP
    assert "UnfreezeInstance(name: str, project?: str | None)" in HELP


def test_bulk_instance_state_uses_literal():
    # Literal renders as `Literal['start', 'stop', 'restart']` per _type_to_str.
    assert (
        "BulkInstanceState(action: Literal['start', 'stop', 'restart'], "
        "project?: str | None)"
    ) in HELP
    assert "    action: Bulk-apply the action to every instance in the project." in HELP


def test_exec_instance_command_bullet():
    assert "ExecInstance(name: str, command: list[str]," in HELP
    # First line of the command bullet:
    assert "    command: Argv list" in HELP


def test_exec_instance_optional_params_marked():
    assert "environment?: dict | None" in HELP
    assert "cwd?: str | None" in HELP
    assert "user?: int | None" in HELP
    assert "group?: int | None" in HELP


def test_cluster_member_state_ops_present():
    assert "EvacuateClusterMember(name: str)" in HELP
    assert "RestoreClusterMember(name: str)" in HELP


def test_project_bullet_shared_with_read():
    assert "    project: Incus project (default project when omitted)." in HELP


def test_schema_bulk_instance_state_action_enum():
    schema = server._build_schema("incus_execute", "BulkInstanceState")
    assert set(schema.get("required", [])) == {"action"}
    action_prop = schema["properties"]["action"]
    # Pydantic renders Literal as an enum in JSON Schema.
    assert action_prop["enum"] == ["start", "stop", "restart"]
    assert (
        action_prop["description"]
        == "Bulk-apply the action to every instance in the project."
    )


def test_schema_stop_instance_shape():
    schema = server._build_schema("incus_execute", "StopInstance")
    assert schema["additionalProperties"] is False
    # Only `name` is required; project/force are optional.
    assert set(schema.get("required", [])) == {"name"}
    assert schema["properties"]["force"]["description"].startswith("Immediate kill")


def test_schema_exec_instance_command_description():
    schema = server._build_schema("incus_execute", "ExecInstance")
    assert schema["properties"]["command"]["description"].startswith("Argv list")
