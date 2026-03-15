from __future__ import annotations

from ..registry import _op
from .groups import incus_delete
from .helpers import _get_client, _ok


# ── Instances ────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_instance(name: str, project: str | None = None):
    """Delete an instance. Irreversible."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/instances/{name}", params=params))


@_op(incus_delete)
def delete_snapshot(name: str, snapshot: str):
    """Delete an instance snapshot."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/snapshots/{snapshot}"))


@_op(incus_delete)
def delete_backup(name: str, backup: str):
    """Delete an instance backup."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/backups/{backup}"))


@_op(incus_delete)
def delete_instance_file(name: str, path: str, project: str | None = None):
    """Delete a file from an instance."""
    params: dict = {"path": path}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/instances/{name}/files", params=params))


@_op(incus_delete)
def delete_instance_log(name: str, filename: str):
    """Delete an instance log file."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/logs/{filename}"))


@_op(incus_delete)
def delete_exec_output(name: str, filename: str):
    """Delete an exec output file."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/logs/exec-output/{filename}"))


@_op(incus_delete)
def delete_instance_template(name: str):
    """Delete instance file templates."""
    return _ok(_get_client().delete(f"/1.0/instances/{name}/metadata/templates"))


@_op(incus_delete)
def clear_console(name: str, project: str | None = None):
    """Clear instance console log."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/instances/{name}/console", params=params))


# ── Images ───────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_image(fingerprint: str, project: str | None = None):
    """Delete an image."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/images/{fingerprint}", params=params))


@_op(incus_delete)
def delete_image_alias(name: str):
    """Delete an image alias."""
    return _ok(_get_client().delete(f"/1.0/images/aliases/{name}"))


# ── Networks ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_network(name: str, project: str | None = None):
    """Delete a network."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/networks/{name}", params=params))


@_op(incus_delete)
def delete_network_forward(network: str, listen_address: str):
    """Delete a network address forward."""
    return _ok(_get_client().delete(f"/1.0/networks/{network}/forwards/{listen_address}"))


@_op(incus_delete)
def delete_load_balancer(network: str, listen_address: str):
    """Delete a network load balancer."""
    return _ok(_get_client().delete(f"/1.0/networks/{network}/load-balancers/{listen_address}"))


@_op(incus_delete)
def delete_network_peer(network: str, peer: str):
    """Delete a network peer."""
    return _ok(_get_client().delete(f"/1.0/networks/{network}/peers/{peer}"))


@_op(incus_delete)
def delete_network_acl(name: str):
    """Delete a network ACL."""
    return _ok(_get_client().delete(f"/1.0/network-acls/{name}"))


@_op(incus_delete)
def delete_network_address_set(name: str):
    """Delete a network address set."""
    return _ok(_get_client().delete(f"/1.0/network-address-sets/{name}"))


@_op(incus_delete)
def delete_network_integration(name: str):
    """Delete a network integration."""
    return _ok(_get_client().delete(f"/1.0/network-integrations/{name}"))


@_op(incus_delete)
def delete_network_zone(zone: str):
    """Delete a network zone."""
    return _ok(_get_client().delete(f"/1.0/network-zones/{zone}"))


@_op(incus_delete)
def delete_zone_record(zone: str, name: str):
    """Delete a DNS record from a network zone."""
    return _ok(_get_client().delete(f"/1.0/network-zones/{zone}/records/{name}"))


# ── Storage ──────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_storage_pool(pool: str, project: str | None = None):
    """Delete a storage pool."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}", params=params))


@_op(incus_delete)
def delete_volume(pool: str, type: str, volume: str, project: str | None = None):
    """Delete a storage volume."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}", params=params))


@_op(incus_delete)
def delete_volume_snapshot(pool: str, type: str, volume: str, snapshot: str):
    """Delete a volume snapshot."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}"))


@_op(incus_delete)
def delete_volume_backup(pool: str, type: str, volume: str, backup: str):
    """Delete a volume backup."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups/{backup}"))


@_op(incus_delete)
def delete_volume_file(pool: str, type: str, volume: str):
    """Delete volume files."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/files"))


@_op(incus_delete)
def delete_bucket(pool: str, bucket: str):
    """Delete a storage bucket."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/buckets/{bucket}"))


@_op(incus_delete)
def delete_bucket_key(pool: str, bucket: str, key: str):
    """Delete a storage bucket key."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys/{key}"))


@_op(incus_delete)
def delete_bucket_backup(pool: str, bucket: str, backup: str):
    """Delete a storage bucket backup."""
    return _ok(_get_client().delete(f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups/{backup}"))


# ── Profiles ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_profile(name: str, project: str | None = None):
    """Delete a profile."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().delete(f"/1.0/profiles/{name}", params=params))


# ── Projects ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_project(name: str, force: bool = False):
    """Delete a project."""
    params = {}
    if force:
        params["force"] = "true"
    return _ok(_get_client().delete(f"/1.0/projects/{name}", params=params))


# ── Cluster ──────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_cluster_member(name: str):
    """Remove a member from the cluster."""
    return _ok(_get_client().delete(f"/1.0/cluster/members/{name}"))


@_op(incus_delete)
def delete_cluster_group(name: str):
    """Delete a cluster group."""
    return _ok(_get_client().delete(f"/1.0/cluster/groups/{name}"))


# ── Certificates ─────────────────────────────────────────────────────


@_op(incus_delete)
def delete_certificate(fingerprint: str):
    """Delete a trusted certificate."""
    return _ok(_get_client().delete(f"/1.0/certificates/{fingerprint}"))


# ── Operations ───────────────────────────────────────────────────────


@_op(incus_delete)
def cancel_operation(id: str):
    """Cancel a background operation."""
    return _ok(_get_client().delete(f"/1.0/operations/{id}"))


# ── Warnings ─────────────────────────────────────────────────────────


@_op(incus_delete)
def delete_warning(uuid: str):
    """Delete a warning."""
    return _ok(_get_client().delete(f"/1.0/warnings/{uuid}"))
