from __future__ import annotations

from typing import Annotated, Any, cast

from pydantic import Field

from ..registry import _UNSET, _op
from ..types import OperationDict
from .groups import incus_delete
from .helpers import _PROJECT_DESC, _get_client, _ok, _qp

# No verify wiring: DELETEs send empty body; _verify_response would no-op
# (plan 7d).

_ProjectAnn = Annotated[str | None, Field(description=_PROJECT_DESC)]
_UNSET_STR = cast(str | None, _UNSET)


# ── Instances ────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_instance(name: str, project: _ProjectAnn = _UNSET_STR) -> OperationDict:
    """Delete an instance. Irreversible."""
    return cast("OperationDict", _ok(_get_client().delete(f"/1.0/instances/{name}", params=_qp(project=project))))


@_op(incus_delete)
def delete_snapshot(name: str, snapshot: str) -> OperationDict:
    """Delete an instance snapshot."""
    return cast("OperationDict", _ok(_get_client().delete(f"/1.0/instances/{name}/snapshots/{snapshot}")))


@_op(incus_delete)
def delete_backup(name: str, backup: str) -> OperationDict:
    """Delete an instance backup."""
    return cast("OperationDict", _ok(_get_client().delete(f"/1.0/instances/{name}/backups/{backup}")))


@_op(incus_delete)
def delete_instance_file(name: str, path: str, project: _ProjectAnn = _UNSET_STR) -> dict[str, Any]:
    """Delete a file from an instance."""
    return _ok(_get_client().delete(
        f"/1.0/instances/{name}/files",
        params=_qp(project=project, path=path),
    ))


@_op(incus_delete)
def delete_instance_log(name: str, filename: str) -> dict[str, Any]:
    """Delete an instance log file."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/logs/{filename}"))


@_op(incus_delete)
def delete_exec_output(name: str, filename: str) -> dict[str, Any]:
    """Delete an exec output file."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/logs/exec-output/{filename}"))


@_op(incus_delete)
def delete_instance_template(name: str) -> dict[str, Any]:
    """Delete instance file templates."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/metadata/templates"))


@_op(incus_delete)
def clear_console(name: str, project: _ProjectAnn = _UNSET_STR) -> dict[str, Any]:
    """Clear instance console log."""
    return _ok(_get_client().delete(
        f"/1.0/instances/{name}/console", params=_qp(project=project),
    ))


# ── Images ───────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_image(fingerprint: str, project: _ProjectAnn = _UNSET_STR) -> OperationDict:
    """Delete an image."""
    return cast("OperationDict", _ok(_get_client().delete(
        f"/1.0/images/{fingerprint}", params=_qp(project=project),
    )))


@_op(incus_delete)
def delete_image_alias(name: str) -> dict[str, Any]:
    """Delete an image alias."""
    return _ok(_get_client().delete(f"/1.0/images/aliases/{name}"))


# ── Networks ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_network(name: str, project: _ProjectAnn = _UNSET_STR) -> dict[str, Any]:
    """Delete a network."""
    return _ok(_get_client().delete(
        f"/1.0/networks/{name}", params=_qp(project=project),
    ))


@_op(incus_delete)
def delete_network_forward(network: str, listen_address: str) -> dict[str, Any]:
    """Delete a network address forward."""
    return _ok(_get_client().delete(f"/1.0/networks/{network}/forwards/{listen_address}"))


@_op(incus_delete)
def delete_load_balancer(network: str, listen_address: str) -> dict[str, Any]:
    """Delete a network load balancer."""
    return _ok(_get_client().delete(f"/1.0/networks/{network}/load-balancers/{listen_address}"))


@_op(incus_delete)
def delete_network_peer(network: str, peer: str) -> dict[str, Any]:
    """Delete a network peer."""
    return _ok(_get_client().delete(f"/1.0/networks/{network}/peers/{peer}"))


@_op(incus_delete)
def delete_network_acl(name: str) -> dict[str, Any]:
    """Delete a network ACL."""
    return _ok(_get_client().delete(f"/1.0/network-acls/{name}"))


@_op(incus_delete)
def delete_network_address_set(name: str) -> dict[str, Any]:
    """Delete a network address set."""
    return _ok(_get_client().delete(f"/1.0/network-address-sets/{name}"))


@_op(incus_delete)
def delete_network_integration(name: str) -> dict[str, Any]:
    """Delete a network integration."""
    return _ok(_get_client().delete(f"/1.0/network-integrations/{name}"))


@_op(incus_delete)
def delete_network_zone(zone: str) -> dict[str, Any]:
    """Delete a network zone."""
    return _ok(_get_client().delete(f"/1.0/network-zones/{zone}"))


@_op(incus_delete)
def delete_zone_record(zone: str, name: str) -> dict[str, Any]:
    """Delete a DNS record from a network zone."""
    return _ok(_get_client().delete(f"/1.0/network-zones/{zone}/records/{name}"))


# ── Storage ──────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_storage_pool(pool: str, project: _ProjectAnn = _UNSET_STR) -> dict[str, Any]:
    """Delete a storage pool."""
    return _ok(_get_client().delete(
        f"/1.0/storage-pools/{pool}", params=_qp(project=project),
    ))


@_op(incus_delete)
def delete_volume(
    pool: str,
    type: str,
    volume: str,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Delete a storage volume."""
    return _ok(_get_client().delete(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}",
        params=_qp(project=project),
    ))


@_op(incus_delete)
def delete_volume_snapshot(pool: str, type: str, volume: str, snapshot: str) -> OperationDict:
    """Delete a volume snapshot."""
    return cast("OperationDict", _ok(_get_client().delete(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}",
    )))


@_op(incus_delete)
def delete_volume_backup(pool: str, type: str, volume: str, backup: str) -> OperationDict:
    """Delete a volume backup."""
    return cast("OperationDict", _ok(_get_client().delete(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups/{backup}",
    )))


@_op(incus_delete)
def delete_volume_file(pool: str, type: str, volume: str) -> dict[str, Any]:
    """Delete volume files."""
    return _ok(_get_client().delete(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/files",
    ))


@_op(incus_delete)
def delete_bucket(pool: str, bucket: str) -> dict[str, Any]:
    """Delete a storage bucket."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/buckets/{bucket}"))


@_op(incus_delete)
def delete_bucket_key(pool: str, bucket: str, key: str) -> dict[str, Any]:
    """Delete a storage bucket key."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys/{key}"))


@_op(incus_delete)
def delete_bucket_backup(pool: str, bucket: str, backup: str) -> OperationDict:
    """Delete a storage bucket backup."""
    return cast("OperationDict", _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups/{backup}")))


# ── Profiles ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_profile(name: str, project: _ProjectAnn = _UNSET_STR) -> dict[str, Any]:
    """Delete a profile."""
    return _ok(_get_client().delete(
        f"/1.0/profiles/{name}", params=_qp(project=project),
    ))


# ── Projects ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_project(
    name: str,
    force: Annotated[
        bool,
        Field(description="Also delete every resource belonging to the project (irreversible)."),
    ] = False,
) -> dict[str, Any]:
    """Delete a project."""
    params: dict[str, str] = {}
    if force:
        params["force"] = "true"
    return _ok(_get_client().delete(f"/1.0/projects/{name}", params=params))


# ── Cluster ──────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_cluster_member(name: str) -> dict[str, Any]:
    """Remove a member from the cluster."""
    return _ok(_get_client().delete(f"/1.0/cluster/members/{name}"))


@_op(incus_delete)
def delete_cluster_group(name: str) -> dict[str, Any]:
    """Delete a cluster group."""
    return _ok(_get_client().delete(f"/1.0/cluster/groups/{name}"))


# ── Certificates ─────────────────────────────────────────────────────


@_op(incus_delete)
def delete_certificate(fingerprint: str) -> dict[str, Any]:
    """Delete a trusted certificate."""
    return _ok(_get_client().delete(f"/1.0/certificates/{fingerprint}"))


# ── Operations ───────────────────────────────────────────────────────


@_op(incus_delete)
def cancel_operation(id: str) -> dict[str, Any]:
    """Cancel a background operation."""
    return _ok(_get_client().delete(f"/1.0/operations/{id}"))


# ── Warnings ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_warning(uuid: str) -> dict[str, Any]:
    """Delete a warning."""
    return _ok(_get_client().delete(f"/1.0/warnings/{uuid}"))
