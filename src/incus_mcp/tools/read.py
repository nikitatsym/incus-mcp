from __future__ import annotations

from ..registry import ROOT, _op
from .groups import incus_read
from .helpers import (
    SLIM_IMAGE,
    SLIM_INSTANCE,
    SLIM_NETWORK,
    SLIM_PROFILE,
    SLIM_PROJECT,
    SLIM_VOLUME,
    _get_client,
    _ok,
    _qp,
    _slim_list,
)


# ── Version ──────────────────────────────────────────────────────────


@_op(ROOT)
def incus_version():
    """Get the Incus MCP server version and service status."""
    from importlib.metadata import version

    server = _get_client().get("/1.0")
    return {
        "mcp": version("incus-mcp"),
        "server": {
            "environment": server.get("environment", {}).get("server_name"),
            "api_version": server.get("api_version"),
        },
    }


# ── Server ───────────────────────────────────────────────────────────


@_op(incus_read)
def get_server():
    """Get server environment and config."""
    return _get_client().get("/1.0")


@_op(incus_read)
def get_resources():
    """Get system resources: CPU, memory, GPU, storage, network, USB, PCI."""
    return _get_client().get("/1.0/resources")


@_op(incus_read)
def get_metrics():
    """Get Prometheus metrics."""
    return _get_client().get("/1.0/metrics")


@_op(incus_read)
def get_metadata_config():
    """Get metadata configuration documentation."""
    return _get_client().get("/1.0/metadata/configuration")


# ── Instances ────────────────────────────────────────────────────────


@_op(incus_read)
def list_instances(project: str | None = None, filter: str | None = None, all_projects: bool = False):
    """List instances (slim: name, status, type, architecture, location, project, created_at)."""
    data = _get_client().get("/1.0/instances", params=_qp(project=project, filter=filter, all_projects=all_projects, recursion=1))
    return _slim_list(data, SLIM_INSTANCE)


@_op(incus_read)
def show_instance(name: str, project: str | None = None):
    """Get full instance details."""
    return _get_client().get(f"/1.0/instances/{name}", params=_qp(project=project))


@_op(incus_read)
def get_instance_state(name: str, project: str | None = None):
    """Get instance state: CPU, memory, disk, network usage."""
    return _get_client().get(f"/1.0/instances/{name}/state", params=_qp(project=project))


@_op(incus_read)
def get_instance_access(name: str):
    """Get instance access information."""
    return _get_client().get(f"/1.0/instances/{name}/access")


@_op(incus_read)
def list_instance_logs(name: str):
    """List instance log files."""
    return _get_client().get(f"/1.0/instances/{name}/logs")


@_op(incus_read)
def get_instance_log(name: str, filename: str):
    """Get a specific instance log file."""
    return _get_client().get(f"/1.0/instances/{name}/logs/{filename}")


@_op(incus_read)
def list_exec_outputs(name: str):
    """List exec output files for an instance."""
    return _get_client().get(f"/1.0/instances/{name}/logs/exec-output")


@_op(incus_read)
def get_exec_output(name: str, filename: str):
    """Get a specific exec output file."""
    return _get_client().get(f"/1.0/instances/{name}/logs/exec-output/{filename}")


@_op(incus_read)
def get_console_output(name: str, project: str | None = None):
    """Get instance console output."""
    return _get_client().get(f"/1.0/instances/{name}/console", params=_qp(project=project))


@_op(incus_read)
def get_instance_file(name: str, path: str, project: str | None = None):
    """Get a file from an instance."""
    return _get_client().get(f"/1.0/instances/{name}/files", params=_qp(project=project, path=path))


@_op(incus_read)
def get_instance_metadata(name: str, project: str | None = None):
    """Get instance image metadata."""
    return _get_client().get(f"/1.0/instances/{name}/metadata", params=_qp(project=project))


@_op(incus_read)
def list_instance_templates(name: str):
    """List instance file templates."""
    return _get_client().get(f"/1.0/instances/{name}/metadata/templates")


# ── Instance Snapshots ───────────────────────────────────────────────


@_op(incus_read)
def list_snapshots(name: str, project: str | None = None):
    """List instance snapshots."""
    return _get_client().get(f"/1.0/instances/{name}/snapshots", params=_qp(project=project, recursion=1))


@_op(incus_read)
def show_snapshot(name: str, snapshot: str):
    """Get snapshot details."""
    return _get_client().get(f"/1.0/instances/{name}/snapshots/{snapshot}")


# ── Instance Backups ─────────────────────────────────────────────────


@_op(incus_read)
def list_backups(name: str):
    """List instance backups."""
    return _get_client().get(f"/1.0/instances/{name}/backups", params=_qp(recursion=1))


@_op(incus_read)
def show_backup(name: str, backup: str):
    """Get backup details."""
    return _get_client().get(f"/1.0/instances/{name}/backups/{backup}")


# ── Images ───────────────────────────────────────────────────────────


@_op(incus_read)
def list_images(project: str | None = None, filter: str | None = None, all_projects: bool = False):
    """List images (slim: fingerprint, type, architecture, size, created_at, description)."""
    data = _get_client().get("/1.0/images", params=_qp(project=project, filter=filter, all_projects=all_projects, recursion=1))
    return _slim_list(data, SLIM_IMAGE)


@_op(incus_read)
def show_image(fingerprint: str, project: str | None = None):
    """Get full image details."""
    return _get_client().get(f"/1.0/images/{fingerprint}", params=_qp(project=project))


@_op(incus_read)
def list_image_aliases(project: str | None = None):
    """List image aliases."""
    return _get_client().get("/1.0/images/aliases", params=_qp(project=project, recursion=1))


@_op(incus_read)
def show_image_alias(name: str):
    """Get image alias details."""
    return _get_client().get(f"/1.0/images/aliases/{name}")


# ── Networks ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_networks(project: str | None = None, filter: str | None = None):
    """List networks (slim: name, type, managed, status)."""
    data = _get_client().get("/1.0/networks", params=_qp(project=project, filter=filter, recursion=1))
    return _slim_list(data, SLIM_NETWORK)


@_op(incus_read)
def show_network(name: str, project: str | None = None):
    """Get full network details."""
    return _get_client().get(f"/1.0/networks/{name}", params=_qp(project=project))


@_op(incus_read)
def get_network_state(name: str):
    """Get network state."""
    return _get_client().get(f"/1.0/networks/{name}/state")


@_op(incus_read)
def get_network_leases(name: str):
    """Get network DHCP leases."""
    return _get_client().get(f"/1.0/networks/{name}/leases")


@_op(incus_read)
def list_network_forwards(network: str):
    """List network address forwards."""
    return _get_client().get(f"/1.0/networks/{network}/forwards", params=_qp(recursion=1))


@_op(incus_read)
def show_network_forward(network: str, listen_address: str):
    """Get network forward details."""
    return _get_client().get(f"/1.0/networks/{network}/forwards/{listen_address}")


@_op(incus_read)
def list_load_balancers(network: str):
    """List network load balancers."""
    return _get_client().get(f"/1.0/networks/{network}/load-balancers", params=_qp(recursion=1))


@_op(incus_read)
def show_load_balancer(network: str, listen_address: str):
    """Get load balancer details."""
    return _get_client().get(f"/1.0/networks/{network}/load-balancers/{listen_address}")


@_op(incus_read)
def get_load_balancer_state(network: str, listen_address: str):
    """Get load balancer state."""
    return _get_client().get(f"/1.0/networks/{network}/load-balancers/{listen_address}/state")


@_op(incus_read)
def list_network_peers(network: str):
    """List network peers."""
    return _get_client().get(f"/1.0/networks/{network}/peers", params=_qp(recursion=1))


@_op(incus_read)
def show_network_peer(network: str, peer: str):
    """Get network peer details."""
    return _get_client().get(f"/1.0/networks/{network}/peers/{peer}")


# ── Network ACLs ─────────────────────────────────────────────────────


@_op(incus_read)
def list_network_acls(project: str | None = None):
    """List network ACLs."""
    return _get_client().get("/1.0/network-acls", params=_qp(project=project, recursion=1))


@_op(incus_read)
def show_network_acl(name: str):
    """Get network ACL details."""
    return _get_client().get(f"/1.0/network-acls/{name}")


@_op(incus_read)
def get_network_acl_log(name: str):
    """Get network ACL log."""
    return _get_client().get(f"/1.0/network-acls/{name}/log")


# ── Network Address Sets ─────────────────────────────────────────────


@_op(incus_read)
def list_network_address_sets():
    """List network address sets."""
    return _get_client().get("/1.0/network-address-sets", params=_qp(recursion=1))


@_op(incus_read)
def show_network_address_set(name: str):
    """Get network address set details."""
    return _get_client().get(f"/1.0/network-address-sets/{name}")


# ── Network Allocations ──────────────────────────────────────────────


@_op(incus_read)
def get_network_allocations():
    """Get network allocations."""
    return _get_client().get("/1.0/network-allocations")


# ── Network Integrations ─────────────────────────────────────────────


@_op(incus_read)
def list_network_integrations():
    """List network integrations."""
    return _get_client().get("/1.0/network-integrations", params=_qp(recursion=1))


@_op(incus_read)
def show_network_integration(name: str):
    """Get network integration details."""
    return _get_client().get(f"/1.0/network-integrations/{name}")


# ── Network Zones ────────────────────────────────────────────────────


@_op(incus_read)
def list_network_zones():
    """List network zones."""
    return _get_client().get("/1.0/network-zones", params=_qp(recursion=1))


@_op(incus_read)
def show_network_zone(zone: str):
    """Get network zone details."""
    return _get_client().get(f"/1.0/network-zones/{zone}")


@_op(incus_read)
def list_zone_records(zone: str):
    """List DNS records in a network zone."""
    return _get_client().get(f"/1.0/network-zones/{zone}/records", params=_qp(recursion=1))


@_op(incus_read)
def show_zone_record(zone: str, name: str):
    """Get DNS record details."""
    return _get_client().get(f"/1.0/network-zones/{zone}/records/{name}")


# ── Storage Pools ────────────────────────────────────────────────────


@_op(incus_read)
def list_storage_pools(project: str | None = None):
    """List storage pools."""
    return _get_client().get("/1.0/storage-pools", params=_qp(project=project, recursion=1))


@_op(incus_read)
def show_storage_pool(pool: str, project: str | None = None):
    """Get storage pool details."""
    return _get_client().get(f"/1.0/storage-pools/{pool}", params=_qp(project=project))


@_op(incus_read)
def get_pool_resources(pool: str):
    """Get storage pool resource usage."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/resources")


# ── Storage Volumes ──────────────────────────────────────────────────


@_op(incus_read)
def list_volumes(pool: str, project: str | None = None, type: str | None = None):
    """List storage volumes (slim: name, type, content_type, location)."""
    path = f"/1.0/storage-pools/{pool}/volumes"
    if type:
        path = f"{path}/{type}"
    data = _get_client().get(path, params=_qp(project=project, recursion=1))
    return _slim_list(data, SLIM_VOLUME)


@_op(incus_read)
def show_volume(pool: str, type: str, volume: str, project: str | None = None):
    """Get full volume details."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}", params=_qp(project=project))


@_op(incus_read)
def get_volume_state(pool: str, type: str, volume: str):
    """Get volume state."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/state")


@_op(incus_read)
def list_volume_snapshots(pool: str, type: str, volume: str):
    """List volume snapshots."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots", params=_qp(recursion=1))


@_op(incus_read)
def show_volume_snapshot(pool: str, type: str, volume: str, snapshot: str):
    """Get volume snapshot details."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}")


@_op(incus_read)
def list_volume_backups(pool: str, type: str, volume: str):
    """List volume backups."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups", params=_qp(recursion=1))


@_op(incus_read)
def show_volume_backup(pool: str, type: str, volume: str, backup: str):
    """Get volume backup details."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups/{backup}")


# ── Storage Buckets ──────────────────────────────────────────────────


@_op(incus_read)
def list_buckets(pool: str):
    """List storage buckets."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/buckets", params=_qp(recursion=1))


@_op(incus_read)
def show_bucket(pool: str, bucket: str):
    """Get storage bucket details."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/buckets/{bucket}")


@_op(incus_read)
def list_bucket_keys(pool: str, bucket: str):
    """List storage bucket keys."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys", params=_qp(recursion=1))


@_op(incus_read)
def show_bucket_key(pool: str, bucket: str, key: str):
    """Get storage bucket key details."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys/{key}")


@_op(incus_read)
def list_bucket_backups(pool: str, bucket: str):
    """List storage bucket backups."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups", params=_qp(recursion=1))


@_op(incus_read)
def show_bucket_backup(pool: str, bucket: str, backup: str):
    """Get storage bucket backup details."""
    return _get_client().get(f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups/{backup}")


# ── Profiles ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_profiles(project: str | None = None):
    """List profiles (slim: name, description)."""
    data = _get_client().get("/1.0/profiles", params=_qp(project=project, recursion=1))
    return _slim_list(data, SLIM_PROFILE)


@_op(incus_read)
def show_profile(name: str, project: str | None = None):
    """Get full profile details."""
    return _get_client().get(f"/1.0/profiles/{name}", params=_qp(project=project))


# ── Projects ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_projects(filter: str | None = None):
    """List projects (slim: name, description)."""
    data = _get_client().get("/1.0/projects", params=_qp(filter=filter, recursion=1))
    return _slim_list(data, SLIM_PROJECT)


@_op(incus_read)
def show_project(name: str):
    """Get full project details."""
    return _get_client().get(f"/1.0/projects/{name}")


@_op(incus_read)
def get_project_access(name: str):
    """Get project access information."""
    return _get_client().get(f"/1.0/projects/{name}/access")


@_op(incus_read)
def get_project_state(name: str):
    """Get project resource usage."""
    return _get_client().get(f"/1.0/projects/{name}/state")


# ── Cluster ──────────────────────────────────────────────────────────


@_op(incus_read)
def get_cluster():
    """Get cluster information."""
    return _get_client().get("/1.0/cluster")


@_op(incus_read)
def list_cluster_members(filter: str | None = None):
    """List cluster members."""
    return _get_client().get("/1.0/cluster/members", params=_qp(filter=filter, recursion=1))


@_op(incus_read)
def show_cluster_member(name: str):
    """Get cluster member details."""
    return _get_client().get(f"/1.0/cluster/members/{name}")


@_op(incus_read)
def get_cluster_member_state(name: str):
    """Get cluster member state."""
    return _get_client().get(f"/1.0/cluster/members/{name}/state")


@_op(incus_read)
def list_cluster_groups():
    """List cluster groups."""
    return _get_client().get("/1.0/cluster/groups", params=_qp(recursion=1))


@_op(incus_read)
def show_cluster_group(name: str):
    """Get cluster group details."""
    return _get_client().get(f"/1.0/cluster/groups/{name}")


# ── Certificates ─────────────────────────────────────────────────────


@_op(incus_read)
def list_certificates(filter: str | None = None):
    """List trusted certificates."""
    return _get_client().get("/1.0/certificates", params=_qp(filter=filter, recursion=1))


@_op(incus_read)
def show_certificate(fingerprint: str):
    """Get certificate details."""
    return _get_client().get(f"/1.0/certificates/{fingerprint}")


# ── Operations ───────────────────────────────────────────────────────


@_op(incus_read)
def list_operations():
    """List background operations."""
    return _get_client().get("/1.0/operations", params=_qp(recursion=1))


@_op(incus_read)
def show_operation(id: str):
    """Get operation details."""
    return _get_client().get(f"/1.0/operations/{id}")


@_op(incus_read)
def wait_operation(id: str):
    """Wait for an operation to complete."""
    return _get_client().get(f"/1.0/operations/{id}/wait")


# ── Warnings ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_warnings():
    """List warnings."""
    return _get_client().get("/1.0/warnings", params=_qp(recursion=1))


@_op(incus_read)
def show_warning(uuid: str):
    """Get warning details."""
    return _get_client().get(f"/1.0/warnings/{uuid}")
