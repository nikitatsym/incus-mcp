"""Step 7 fixtures: tools/admin.py v2.5 annotations + verify wiring.

`Literal["new", "acknowledged"]` on warning.status renders in help; verify
wiring on `update_server_config` catches silent-drop on `config`.
"""

from __future__ import annotations

import pytest

import incus_mcp.server as server
from incus_mcp.tools import admin


HELP = server._build_help("incus_admin")


def _sync(metadata):
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": metadata,
    }


def test_no_unset_leak_in_help():
    assert "_Unset" not in HELP
    assert "_UNSET" not in HELP


def test_update_server_config_signature():
    assert "UpdateServerConfig(config: dict)" in HELP


def test_patch_server_config_signature():
    assert "PatchServerConfig(config: dict)" in HELP


def test_update_warning_uses_literal():
    assert (
        "UpdateWarning(uuid: str, status: Literal['new', 'acknowledged'])"
    ) in HELP


def test_patch_warning_status_optional_literal():
    assert (
        "PatchWarning(uuid: str, status?: Literal['new', 'acknowledged'] | None)"
    ) in HELP


def test_schema_update_warning_status_enum():
    schema = server._build_schema("incus_admin", "UpdateWarning")
    assert set(schema.get("required", [])) == {"uuid", "status"}
    status_prop = schema["properties"]["status"]
    assert status_prop["enum"] == ["new", "acknowledged"]


def test_schema_update_server_config_required():
    schema = server._build_schema("incus_admin", "UpdateServerConfig")
    assert set(schema.get("required", [])) == {"config"}
    assert schema["additionalProperties"] is False


# ── Verify wiring on update_server_config ─────────────────────────────


def test_update_server_config_silent_drop_raises(stub_client, respx_mock):
    respx_mock.put("/1.0").respond(
        200, json=_sync({"config": {}, "environment": {}}),
    )
    with pytest.raises(ValueError, match=r"config\.core\.bogus"):
        admin.update_server_config(config={"core.bogus": "x"})


def test_update_server_config_verify_pass(stub_client, respx_mock):
    respx_mock.put("/1.0").respond(
        200,
        json=_sync({"config": {"core.https_address": ":8443"}}),
    )
    admin.update_server_config(config={"core.https_address": ":8443"})


def test_patch_server_config_verify_wired(stub_client, respx_mock):
    respx_mock.patch("/1.0").respond(
        200,
        json=_sync({"config": {}}),
    )
    with pytest.raises(ValueError, match=r"config\.core\.trust_password"):
        admin.patch_server_config(config={"core.trust_password": "s3cret"})


def test_update_warning_verify_pass(stub_client, respx_mock):
    respx_mock.put("/1.0/warnings/uuid-1").respond(
        200,
        json=_sync({"status": "acknowledged", "uuid": "uuid-1"}),
    )
    admin.update_warning(uuid="uuid-1", status="acknowledged")


def test_patch_warning_omit_status(stub_client, respx_mock):
    import json
    route = respx_mock.patch("/1.0/warnings/uuid-1").respond(
        200, json=_sync({}),
    )
    admin.patch_warning(uuid="uuid-1")
    body = json.loads(route.calls[0].request.content)
    assert body == {}


def test_patch_warning_explicit_status(stub_client, respx_mock):
    import json
    route = respx_mock.patch("/1.0/warnings/uuid-1").respond(
        200,
        json=_sync({"status": "new"}),
    )
    admin.patch_warning(uuid="uuid-1", status="new")
    body = json.loads(route.calls[0].request.content)
    assert body == {"status": "new"}


# ── Adversarial: attack the Literal enforcement ────────────────────────


async def test_update_warning_invalid_status_rejected(stub_client, respx_mock):
    # Adversarial: Literal must reject before HTTP; widening back to `str`
    # would fire the route and fail the assertion.
    route = respx_mock.put("/1.0/warnings/uuid-1").respond(200, json=_sync({}))
    with pytest.raises(ValueError, match="status"):
        await server._dispatch(
            "UpdateWarning",
            "incus_admin",
            {"uuid": "uuid-1", "status": "dismissed"},
        )
    assert not route.called


async def test_patch_warning_invalid_status_rejected(stub_client, respx_mock):
    route = respx_mock.patch("/1.0/warnings/uuid-1").respond(200, json=_sync({}))
    with pytest.raises(ValueError, match="status"):
        await server._dispatch(
            "PatchWarning",
            "incus_admin",
            {"uuid": "uuid-1", "status": "dismissed"},
        )
    assert not route.called
