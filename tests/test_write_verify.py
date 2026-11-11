"""Step 6 fixtures: verify wiring + pending-verify registry for write ops.

Every test uses `stub_client` + `respx_mock` (no real HTTP). Responses are
wrapped in Incus envelope shape so the client's `_handle` unwraps to the
metadata dict verify sees.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time

import pytest

from incus_mcp import server
from incus_mcp.tools import delete, helpers, read, write


def _sync(metadata):
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": metadata,
    }


def _async(op_id, extra=None):
    op = {
        "id": op_id,
        "class": "task",
        "status": "Running",
        "status_code": 103,
        "metadata": extra or {},
    }
    return {
        "type": "async",
        "status": "Operation created",
        "status_code": 100,
        "operation": f"/1.0/operations/{op_id}",
        "metadata": op,
    }


# -- Sync verify: Incus answers {}, the op reads the resource back -----


def test_sync_silent_drop_raises_with_nested_path(stub_client, respx_mock):
    respx_mock.put("/1.0/networks/n0").respond(200, json=_sync({}))
    respx_mock.get("/1.0/networks/n0").respond(
        200, json=_sync({"name": "n0", "config": {}}),
    )
    with pytest.raises(ValueError, match=r"config\.ipv4\.address"):
        write.update_network(name="n0", config={"ipv4.address": "10.0.0.1/24"})


def test_sync_verify_pass(stub_client, respx_mock):
    respx_mock.put("/1.0/networks/n0").respond(200, json=_sync({}))
    respx_mock.get("/1.0/networks/n0").respond(
        200, json=_sync({"name": "n0", "config": {"ipv4.address": "10.0.0.1/24"}}),
    )
    write.update_network(name="n0", config={"ipv4.address": "10.0.0.1/24"})


def test_sync_readback_keeps_project(stub_client, respx_mock):
    respx_mock.patch("/1.0/networks/n0", params={"project": "p1"}).respond(
        200, json=_sync({}),
    )
    readback = respx_mock.get("/1.0/networks/n0", params={"project": "p1"}).respond(
        200, json=_sync({"name": "n0", "config": {"ipv4.nat": "true"}}),
    )
    write.patch_network(name="n0", config={"ipv4.nat": "true"}, project="p1")
    assert readback.called


def test_sync_readback_skips_cleared_values(stub_client, respx_mock):
    # "" and null clear a value, so the read-back legitimately lacks them.
    respx_mock.put("/1.0/profiles/p0").respond(200, json=_sync({}))
    respx_mock.get("/1.0/profiles/p0").respond(
        200, json=_sync({"name": "p0", "config": {"limits.cpu": "2"}}),
    )
    write.update_profile(
        name="p0", config={"limits.cpu": "2", "limits.memory": ""}, description=None,
    )


def test_create_volume_reads_created_volume_back(stub_client, respx_mock):
    respx_mock.post("/1.0/storage-pools/default/volumes").respond(200, json=_sync({}))
    respx_mock.get("/1.0/storage-pools/default/volumes/custom/v0").respond(
        200, json=_sync({"name": "v0", "type": "custom", "config": {}}),
    )
    with pytest.raises(ValueError, match=r"config\.size"):
        write.create_volume(pool="default", name="v0", config={"size": "1GiB"})


_PEM = "-----BEGIN CERTIFICATE-----\nAAEC\n-----END CERTIFICATE-----\n"
_PEM_FP = hashlib.sha256(b"\x00\x01\x02").hexdigest()

# (write call, POST path, path of the written resource). Incus answers each
# of these with a null body, so only a read-back can see a dropped key.
_SYNC_CREATES_AND_RENAMES = [
    pytest.param(
        lambda: write.create_image_alias(name="a0", target="fp"),
        "/1.0/images/aliases", "/1.0/images/aliases/a0", id="create_image_alias",
    ),
    pytest.param(
        lambda: write.rename_image_alias(name="a0", new_name="a1"),
        "/1.0/images/aliases/a0", "/1.0/images/aliases/a1", id="rename_image_alias",
    ),
    pytest.param(
        lambda: write.create_network(name="n0"),
        "/1.0/networks", "/1.0/networks/n0", id="create_network",
    ),
    pytest.param(
        lambda: write.rename_network(name="n0", new_name="n1"),
        "/1.0/networks/n0", "/1.0/networks/n1", id="rename_network",
    ),
    pytest.param(
        lambda: write.create_network_forward(network="n0", listen_address="10.0.0.1"),
        "/1.0/networks/n0/forwards", "/1.0/networks/n0/forwards/10.0.0.1",
        id="create_network_forward",
    ),
    pytest.param(
        lambda: write.create_load_balancer(network="n0", listen_address="10.0.0.2"),
        "/1.0/networks/n0/load-balancers", "/1.0/networks/n0/load-balancers/10.0.0.2",
        id="create_load_balancer",
    ),
    pytest.param(
        lambda: write.create_network_peer(network="n0", name="p0", target_network="n9"),
        "/1.0/networks/n0/peers", "/1.0/networks/n0/peers/p0", id="create_network_peer",
    ),
    pytest.param(
        lambda: write.create_network_acl(name="acl0"),
        "/1.0/network-acls", "/1.0/network-acls/acl0", id="create_network_acl",
    ),
    pytest.param(
        lambda: write.rename_network_acl(name="acl0", new_name="acl1"),
        "/1.0/network-acls/acl0", "/1.0/network-acls/acl1", id="rename_network_acl",
    ),
    pytest.param(
        lambda: write.create_network_address_set(name="as0"),
        "/1.0/network-address-sets", "/1.0/network-address-sets/as0",
        id="create_network_address_set",
    ),
    pytest.param(
        lambda: write.rename_network_address_set(name="as0", new_name="as1"),
        "/1.0/network-address-sets/as0", "/1.0/network-address-sets/as1",
        id="rename_network_address_set",
    ),
    pytest.param(
        lambda: write.create_network_integration(name="i0", type="ovn"),
        "/1.0/network-integrations", "/1.0/network-integrations/i0",
        id="create_network_integration",
    ),
    pytest.param(
        lambda: write.rename_network_integration(name="i0", new_name="i1"),
        "/1.0/network-integrations/i0", "/1.0/network-integrations/i1",
        id="rename_network_integration",
    ),
    pytest.param(
        lambda: write.create_network_zone(name="z.example"),
        "/1.0/network-zones", "/1.0/network-zones/z.example", id="create_network_zone",
    ),
    pytest.param(
        lambda: write.create_zone_record(zone="z.example", name="www"),
        "/1.0/network-zones/z.example/records", "/1.0/network-zones/z.example/records/www",
        id="create_zone_record",
    ),
    pytest.param(
        lambda: write.create_storage_pool(name="sp0", driver="dir"),
        "/1.0/storage-pools", "/1.0/storage-pools/sp0", id="create_storage_pool",
    ),
    pytest.param(
        lambda: write.rename_volume(pool="default", type="custom", volume="v0", new_name="v1"),
        "/1.0/storage-pools/default/volumes/custom/v0",
        "/1.0/storage-pools/default/volumes/custom/v1", id="rename_volume",
    ),
    pytest.param(
        lambda: write.create_bucket(pool="default", name="b0"),
        "/1.0/storage-pools/default/buckets", "/1.0/storage-pools/default/buckets/b0",
        id="create_bucket",
    ),
    pytest.param(
        lambda: write.create_profile(name="p0"),
        "/1.0/profiles", "/1.0/profiles/p0", id="create_profile",
    ),
    pytest.param(
        lambda: write.rename_profile(name="p0", new_name="p1"),
        "/1.0/profiles/p0", "/1.0/profiles/p1", id="rename_profile",
    ),
    pytest.param(
        lambda: write.create_project(name="pr0"),
        "/1.0/projects", "/1.0/projects/pr0", id="create_project",
    ),
    pytest.param(
        lambda: write.rename_cluster_member(name="m0", new_name="m1"),
        "/1.0/cluster/members/m0", "/1.0/cluster/members/m1", id="rename_cluster_member",
    ),
    pytest.param(
        lambda: write.create_cluster_group(name="g0"),
        "/1.0/cluster/groups", "/1.0/cluster/groups/g0", id="create_cluster_group",
    ),
    pytest.param(
        lambda: write.rename_cluster_group(name="g0", new_name="g1"),
        "/1.0/cluster/groups/g0", "/1.0/cluster/groups/g1", id="rename_cluster_group",
    ),
    pytest.param(
        lambda: write.add_certificate(certificate=_PEM),
        "/1.0/certificates", f"/1.0/certificates/{_PEM_FP}", id="add_certificate",
    ),
]


@pytest.mark.parametrize(("call", "post_path", "resource_path"), _SYNC_CREATES_AND_RENAMES)
def test_sync_create_or_rename_reads_the_written_resource_back(
    stub_client, respx_mock, call, post_path, resource_path,
):
    respx_mock.post(post_path).respond(200, json=_sync(None))
    respx_mock.get(resource_path).respond(200, json=_sync({}))
    with pytest.raises(ValueError, match="silently dropped"):
        call()


def test_create_bucket_checks_the_bucket_not_the_returned_key(stub_client, respx_mock):
    # Incus answers with the bucket's admin key, which has no `config`.
    key = {"name": "admin", "role": "admin", "access-key": "ak", "secret-key": "sk"}
    respx_mock.post("/1.0/storage-pools/default/buckets").respond(200, json=_sync(key))
    respx_mock.get("/1.0/storage-pools/default/buckets/b0").respond(
        200, json=_sync({"name": "b0", "config": {"size": "1GiB"}, "description": ""}),
    )
    assert write.create_bucket(pool="default", name="b0", config={"size": "1GiB"}) == key


def test_update_cluster_disable_succeeds_on_empty_answer(stub_client, respx_mock):
    # Disabling answers {} and restarts Incus; there is no resource to read back.
    respx_mock.get("/1.0/cluster").respond(200, json=_sync({"server_name": "n1", "enabled": True}))
    respx_mock.put("/1.0/cluster").respond(200, json=_sync({}))
    assert write.update_cluster(enabled=False) == {}


def test_update_cluster_refuses_disable_on_a_standalone_server(stub_client, respx_mock):
    # On a server that is not clustered Incus answers a disable by resetting its database.
    respx_mock.get("/1.0/cluster").respond(200, json=_sync({"server_name": "", "enabled": False}))
    put = respx_mock.put("/1.0/cluster").respond(200, json=_sync({}))
    with pytest.raises(ValueError, match="not clustered"):
        write.update_cluster(enabled=False)
    assert not put.called


async def test_update_cluster_without_enabled_is_rejected_before_any_request(
    stub_client, respx_mock,
):
    # Incus reads a missing `enabled` as false, which disables clustering.
    result = await server._dispatch("UpdateCluster", "incus_write", {"cluster_address": "x:8443"})
    assert "enabled" in result["error"]


def test_request_join_token_returns_the_token_operation(stub_client, respx_mock):
    token = {
        "id": "op-tok", "class": "token", "status": "Running", "status_code": 103,
        "metadata": {"serverName": "node2", "secret": "s", "fingerprint": "f", "addresses": []},
    }
    respx_mock.post("/1.0/cluster/members").respond(
        202,
        json={
            "type": "async", "status": "Operation created", "status_code": 100,
            "operation": "/1.0/operations/op-tok", "metadata": token,
        },
    )
    assert write.request_join_token(name="node2") == token


_TEST_CERT = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIBZzCCAQygAwIBAgIUZekrxAozJM/6FkRntbeP4qV88uMwCgYIKoZIzj0EAwIw\n"
    "GTEXMBUGA1UEAwwOaW5jdXMtbWNwLXRlc3QwHhcNMjYxMTExMTczOTQ0WhcNMzYx\n"
    "MTA4MTczOTQ0WjAZMRcwFQYDVQQDDA5pbmN1cy1tY3AtdGVzdDBZMBMGByqGSM49\n"
    "AgEGCCqGSM49AwEHA0IABHRvNvW6NB3Ko82czr+SEV5efiT3x2o5iJJWjYlId/zj\n"
    "iobWY/SvuhGEvmTw8n4G+ommFEU6+se0pCVsTlQVJZ+jMjAwMB0GA1UdDgQWBBRK\n"
    "/xUlDSNSgZZ60bYvRmHEW1PqDDAPBgNVHRMBAf8EBTADAQH/MAoGCCqGSM49BAMC\n"
    "A0kAMEYCIQCzKqHx+NSeQnsi7JTW5Jd5b4tWMDe1TcK+KEk0m5chLgIhALKhV7Kq\n"
    "Sq6Vtud2xkWQ9XVnKr6hzolLoj3S8KvFcA16\n"
    "-----END CERTIFICATE-----\n"
)
# sha256 of the DER, from `openssl x509 -outform der | sha256sum`.
_TEST_CERT_FP = "0603f5d3f00c5b3041b7ec97f0a36d9e9ab29e0b2dead834e2146d55baeb1ead"


@pytest.mark.parametrize(
    "pem",
    [
        pytest.param(_TEST_CERT, id="plain"),
        pytest.param(
            _TEST_CERT.replace("-----\n", "-----\nComment: review\n\n", 1), id="pem-header",
        ),
        pytest.param(_TEST_CERT.replace("CERTIFICATE", "TRUSTED CERTIFICATE"), id="other-label"),
        pytest.param("subject=CN = incus-mcp-test\n" + _TEST_CERT, id="leading-text"),
    ],
)
def test_add_certificate_reads_back_under_the_fingerprint_incus_computes(
    stub_client, respx_mock, pem,
):
    # Incus decodes with Go's pem.Decode and fingerprints the first block's DER.
    respx_mock.post("/1.0/certificates").respond(200, json=_sync(None))
    readback = respx_mock.get(f"/1.0/certificates/{_TEST_CERT_FP}").respond(
        200, json=_sync({"certificate": _TEST_CERT, "type": "client", "restricted": False}),
    )
    write.add_certificate(certificate=pem)
    assert readback.called


@pytest.mark.parametrize(
    ("sent", "stored"),
    [
        pytest.param("0:0:0:0:0:ffff:c000:027c", "192.0.2.124", id="ipv4-mapped"),
        pytest.param("2001:DB8:0:0:0:0:0:1", "2001:db8::1", id="ipv6-long-form"),
    ],
)
def test_create_network_forward_reads_back_under_the_canonical_address(
    stub_client, respx_mock, sent, stored,
):
    # Incus stores the listen address in Go's net.IP form; GET matches it literally.
    respx_mock.post("/1.0/networks/n0/forwards").respond(200, json=_sync(None))
    readback = respx_mock.get(f"/1.0/networks/n0/forwards/{stored}").respond(
        200, json=_sync({"listen_address": stored, "description": "", "config": {}, "ports": []}),
    )
    write.create_network_forward(network="n0", listen_address=sent)
    assert readback.called


def test_create_storage_pool_does_not_expect_source_wipe_back(stub_client, respx_mock):
    # Incus clears source.wipe once it has wiped the disk.
    respx_mock.post("/1.0/storage-pools").respond(200, json=_sync(None))
    respx_mock.get("/1.0/storage-pools/sp0").respond(
        200,
        json=_sync({
            "name": "sp0", "driver": "zfs", "description": "",
            "config": {"source": "/dev/sdb", "zfs.pool_name": "sp0"},
        }),
    )
    write.create_storage_pool(
        name="sp0", driver="zfs", config={"source": "/dev/sdb", "source.wipe": "true"},
    )


# ── Body-builder audit: omit vs explicit-None ─────────────────────────


def test_update_instance_omit_drops_optionals_from_body(stub_client, respx_mock):
    route = respx_mock.put("/1.0/instances/i0").respond(200, json=_sync({}))
    write.update_instance(name="i0")
    body = json.loads(route.calls[0].request.content)
    for k in ("config", "devices", "profiles", "description"):
        assert k not in body


def test_update_instance_explicit_none_passes_as_json_null(stub_client, respx_mock):
    # Mock echoes back the null-valued keys so verify's presence check passes.
    route = respx_mock.put("/1.0/instances/i0").respond(
        200,
        json=_sync({
            "config": None,
            "devices": None,
            "profiles": None,
            "description": None,
        }),
    )
    write.update_instance(
        name="i0",
        config=None,
        devices=None,
        profiles=None,
        description=None,
    )
    body = json.loads(route.calls[0].request.content)
    assert body == {
        "config": None,
        "devices": None,
        "profiles": None,
        "description": None,
    }


def test_update_instance_mixed_omit_and_explicit(stub_client, respx_mock):
    route = respx_mock.put("/1.0/instances/i0").respond(
        200,
        json=_sync({
            "config": {"limits.cpu": "2", "volatile.uuid": "z"},
            "description": None,
        }),
    )
    write.update_instance(name="i0", config={"limits.cpu": "2"}, description=None)
    body = json.loads(route.calls[0].request.content)
    assert body == {"config": {"limits.cpu": "2"}, "description": None}


# ── Query-param drop-both (project on a read op via _qp) ──────────────


def test_list_instances_project_none_drops_qp(stub_client, respx_mock):
    route = respx_mock.get("/1.0/instances").respond(200, json=_sync([]))
    read.list_instances(project=None)
    assert "project" not in str(route.calls[0].request.url)


def test_list_instances_project_empty_drops_qp(stub_client, respx_mock):
    route = respx_mock.get("/1.0/instances").respond(200, json=_sync([]))
    read.list_instances(project="")
    assert "project" not in str(route.calls[0].request.url)


def test_list_instances_project_present(stub_client, respx_mock):
    route = respx_mock.get("/1.0/instances").respond(200, json=_sync([]))
    read.list_instances(project="p")
    assert "project=p" in str(route.calls[0].request.url)


# ── Pending-verify registration ──────────────────────────────────────


def test_create_instance_registers_target_and_qp(stub_client, respx_mock):
    route = respx_mock.post("/1.0/instances").respond(200, json=_async("op-uuid"))
    write.create_instance(
        name="i0",
        source={"type": "none"},
        project="p",
        target="node2",
    )
    assert "target=node2" in str(route.calls[0].request.url)
    assert "op-uuid" in helpers._pending_verify
    sent, target_path, target_qp, _ = helpers._pending_verify["op-uuid"]
    assert target_path == "/1.0/instances/i0"
    # `target` places the instance; GET /1.0/instances/{name} ignores it.
    assert target_qp == {"project": "p"}
    assert sent["name"] == "i0"
    assert sent["source"] == {"type": "none"}


def test_create_instance_no_qp_when_project_omitted(stub_client, respx_mock):
    respx_mock.post("/1.0/instances").respond(200, json=_async("op-noqp"))
    write.create_instance(name="i1", source={"type": "none"})
    _, _, target_qp, _ = helpers._pending_verify["op-noqp"]
    assert target_qp == {}


def test_create_image_from_source_skips_register(stub_client, respx_mock):
    respx_mock.post("/1.0/images").respond(200, json=_async("op-image"))
    write.create_image(source={"type": "url", "url": "http://x"})
    assert "op-image" not in helpers._pending_verify


def test_rename_instance_registers_new_path(stub_client, respx_mock):
    respx_mock.post("/1.0/instances/old").respond(200, json=_async("op-rename"))
    write.rename_instance(name="old", new_name="new")
    assert "op-rename" in helpers._pending_verify
    _, target_path, _, _ = helpers._pending_verify["op-rename"]
    assert target_path == "/1.0/instances/new"


def test_create_bucket_registers_bucket_path_when_async(stub_client, respx_mock):
    respx_mock.post("/1.0/storage-pools/default/buckets").respond(
        200, json=_async("op-bucket"),
    )
    write.create_bucket(pool="default", name="b0")
    _, target_path, _, _ = helpers._pending_verify["op-bucket"]
    assert target_path == "/1.0/storage-pools/default/buckets/b0"


def test_sync_response_does_not_register(stub_client, respx_mock):
    respx_mock.put("/1.0/networks/n0").respond(200, json=_sync({}))
    respx_mock.get("/1.0/networks/n0").respond(
        200, json=_sync({"name": "n0", "config": {"x": "y"}}),
    )
    before = set(helpers._pending_verify)
    write.update_network(name="n0", config={"x": "y"})
    assert set(helpers._pending_verify) == before


# ── TTL reap on registration ─────────────────────────────────────────


def test_ttl_reaps_stale_entries_on_next_register(stub_client, respx_mock, monkeypatch):
    current = [1000.0]
    monkeypatch.setattr(helpers.time, "time", lambda: current[0])
    for op_id in ("a", "b", "c"):
        respx_mock.post("/1.0/instances").respond(200, json=_async(op_id))
        write.create_instance(name=f"i-{op_id}", source={"type": "none"})
    assert set(helpers._pending_verify) == {"a", "b", "c"}
    current[0] = 1000.0 + helpers._PENDING_VERIFY_TTL + 1.0
    respx_mock.post("/1.0/instances").respond(200, json=_async("d"))
    write.create_instance(name="i-d", source={"type": "none"})
    assert set(helpers._pending_verify) == {"d"}


# ── Concurrent register + drain ──────────────────────────────────────


class _InterleavingDict(dict):
    """Runs `hook` once, right after the first item of the next items() walk."""

    def __init__(self, entries, hook):
        super().__init__(entries)
        self._hook = hook

    def items(self):
        it = iter(super().items())
        yield next(it)
        self._hook()
        yield from it


def test_drain_waits_for_register_reap(monkeypatch):
    # Write ops register from worker threads while waiters drain on the loop.
    # This drain lands mid-way through the reap walk; unguarded, it pops the
    # dict under the iterator and the register raises RuntimeError.
    drained = []
    drainer = threading.Thread(
        target=lambda: drained.append(helpers._drain_pending_verify("op-old")),
    )

    def drain_concurrently():
        drainer.start()
        drainer.join(timeout=0.2)

    entry = ({"k": "v"}, "/1.0/instances/old", {}, time.time())
    pending = _InterleavingDict({"op-old": entry, "op-other": entry}, drain_concurrently)
    monkeypatch.setattr(helpers, "_pending_verify", pending)

    helpers._register_pending_verify({"class": "task", "id": "op-new"}, {"k": "v"}, "/1.0/x")
    drainer.join()

    assert drained == [({"k": "v"}, "/1.0/instances/old", {})]
    assert set(pending) == {"op-other", "op-new"}


# ── Root-skip is root-only; nested keys are real config ──────────────


def test_root_source_is_skipped_at_root(stub_client, respx_mock):
    # create_instance sends `source` at root; the created-resource GET
    # doesn't echo it. Root skip must silence this.
    respx_mock.post("/1.0/instances").respond(
        200,
        json=_sync({"name": "i0", "type": "container"}),
    )
    # No raise:
    write.create_instance(name="i0", source={"type": "image", "alias": "u"})


def test_nested_devices_source_drop_raises(stub_client, respx_mock):
    # `source` inside devices.<name> is a real config value - NOT skipped.
    respx_mock.patch("/1.0/instances/i0").respond(200, json=_sync({}))
    respx_mock.get("/1.0/instances/i0").respond(
        200, json=_sync({"devices": {"root": {}}}),
    )
    with pytest.raises(ValueError, match=r"devices\.root\.source"):
        write.patch_instance(name="i0", devices={"root": {"source": "/dev/xvda"}})


def test_async_readback_skips_cleared_values(stub_client, respx_mock):
    respx_mock.post("/1.0/instances").respond(200, json=_async("op-clr"))
    write.create_instance(
        name="i0", source={"type": "none"}, config={"user.a": "", "user.b": "1"},
    )
    respx_mock.get("/1.0/operations/op-clr/wait").respond(
        200, json=_sync({"id": "op-clr", "class": "task", "status_code": 200}),
    )
    respx_mock.get("/1.0/instances/i0").respond(
        200, json=_sync({"name": "i0", "type": "container", "config": {"user.b": "1"}}),
    )
    read.wait_operation("op-clr")


# -- update_certificate: the stored type goes back unchanged ----------


def test_update_certificate_sends_stored_type(stub_client, respx_mock):
    respx_mock.get("/1.0/certificates/fp0").respond(
        200, json=_sync({"name": "old", "type": "metrics", "restricted": False}),
    )
    put = respx_mock.put("/1.0/certificates/fp0").respond(200, json=_sync({}))
    write.update_certificate(fingerprint="fp0", name="new")
    assert json.loads(put.calls[0].request.content) == {"type": "metrics", "name": "new"}


def test_update_certificate_reads_back_under_new_fingerprint(stub_client, respx_mock):
    pem = "-----BEGIN CERTIFICATE-----\nAAEC\n-----END CERTIFICATE-----\n"
    new_fp = hashlib.sha256(b"\x00\x01\x02").hexdigest()
    respx_mock.get("/1.0/certificates/fp0").respond(200, json=_sync({"type": "client"}))
    respx_mock.put("/1.0/certificates/fp0").respond(200, json=_sync({}))
    readback = respx_mock.get(f"/1.0/certificates/{new_fp}").respond(
        200, json=_sync({"type": "client", "certificate": pem}),
    )
    write.update_certificate(fingerprint="fp0", certificate=pem)
    assert readback.called


def test_delete_volume_file_sends_path(stub_client, respx_mock):
    route = respx_mock.delete("/1.0/storage-pools/default/volumes/custom/v0/files").respond(
        200, json=_sync({}),
    )
    delete.delete_volume_file(pool="default", type="custom", volume="v0", path="/etc/x")
    assert route.calls[0].request.url.params["path"] == "/etc/x"
