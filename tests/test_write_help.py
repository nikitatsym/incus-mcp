"""Step 6 fixtures: tools/write.py v2.5 annotations render in help + schema."""

from __future__ import annotations

import json

import incus_mcp.server as server


HELP = server._build_help("incus_write")


def test_no_unset_leak_in_help():
    assert "_Unset" not in HELP
    assert "_UNSET" not in HELP


def test_help_includes_create_instance():
    assert "CreateInstance(" in HELP


def test_create_instance_required_params_bare():
    # `name: str, source: dict` are required — render as bare typed params.
    assert "name: str" in HELP
    assert "source: dict" in HELP


def test_create_instance_source_bullet():
    assert "source: Source spec:" in HELP


def test_create_instance_config_bullet():
    assert "config: Config namespace map" in HELP


def test_create_instance_devices_bullet():
    assert "devices: Device map keyed by device name" in HELP


def test_create_instance_profiles_bullet():
    assert "profiles: Profile names to apply" in HELP


def test_create_instance_target_bullet():
    assert "target: Target cluster member" in HELP


def test_create_snapshot_stateful_bullet():
    assert "stateful: Include runtime memory state" in HELP


def test_optional_params_marked_with_question_mark():
    # Every _UNSET-defaulted param renders with `?` after the name.
    assert "project?: str | None" in HELP
    assert "config?: dict | None" in HELP


def test_schema_create_instance_shape():
    schema = server._build_schema("incus_write", "CreateInstance")
    assert schema["additionalProperties"] is False
    assert set(schema.get("required", [])) == {"name", "source"}
    assert "_Unset" not in json.dumps(schema)


def test_schema_source_description_populated():
    schema = server._build_schema("incus_write", "CreateInstance")
    assert schema["properties"]["source"]["description"].startswith("Source spec")


def test_schema_config_description_populated():
    schema = server._build_schema("incus_write", "CreateInstance")
    assert schema["properties"]["config"]["description"].startswith(
        "Config namespace map"
    )


def test_schema_update_network_has_only_optional_fields():
    schema = server._build_schema("incus_write", "UpdateNetwork")
    # `name` is required; config / description / project all optional
    assert set(schema.get("required", [])) == {"name"}
    assert schema["additionalProperties"] is False


def test_search_finds_create_ops():
    out = server._build_help("incus_write", search="create")
    for op in ("CreateInstance", "CreateNetwork", "CreateVolume"):
        assert op in out


def test_rename_ops_have_new_name_param():
    assert "RenameInstance(name: str, new_name: str)" in HELP
