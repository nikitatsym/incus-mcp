from __future__ import annotations

from ..registry import _op
from .groups import incus_write
from .helpers import _get_client, _ok


# ── Instances ────────────────────────────────────────────────────────


@_op(incus_write)
def create_instance(name: str, source: dict, type: str = "container", project: str | None = None,
                    profiles: list[str] | None = None, config: dict | None = None,
                    devices: dict | None = None, description: str | None = None,
                    target: str | None = None):
    """Create a new instance. source: {"type": "image", "alias": "ubuntu/24.04"} or {"type": "none"}. Async."""
    body: dict = {"name": name, "source": source, "type": type}
    if profiles is not None:
        body["profiles"] = profiles
    if config is not None:
        body["config"] = config
    if devices is not None:
        body["devices"] = devices
    if description is not None:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    if target:
        params["target"] = target
    return _ok(_get_client().post("/1.0/instances", json=body, params=params))


@_op(incus_write)
def update_instance(name: str, config: dict | None = None, devices: dict | None = None,
                    profiles: list[str] | None = None, description: str | None = None,
                    project: str | None = None):
    """Update instance configuration (full replace). Use PATCH for partial update."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if devices is not None:
        body["devices"] = devices
    if profiles is not None:
        body["profiles"] = profiles
    if description is not None:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/instances/{name}", json=body, params=params))


@_op(incus_write)
def patch_instance(name: str, config: dict | None = None, devices: dict | None = None,
                   profiles: list[str] | None = None, description: str | None = None,
                   project: str | None = None):
    """Partially update instance configuration."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if devices is not None:
        body["devices"] = devices
    if profiles is not None:
        body["profiles"] = profiles
    if description is not None:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().patch(f"/1.0/instances/{name}", json=body, params=params))


@_op(incus_write)
def rename_instance(name: str, new_name: str):
    """Rename an instance (also used for move/migrate)."""
    return _ok(_get_client().post(f"/1.0/instances/{name}", json={"name": new_name}))


@_op(incus_write)
def update_instance_metadata(name: str, metadata: dict, project: str | None = None):
    """Update instance image metadata."""
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/instances/{name}/metadata", json=metadata, params=params))


@_op(incus_write)
def upload_instance_file(name: str, path: str, content: str, project: str | None = None,
                         uid: int | None = None, gid: int | None = None,
                         mode: str | None = None, file_type: str | None = None):
    """Upload a file to an instance. content is the file body as text."""
    params: dict = {"path": path}
    if project:
        params["project"] = project
    headers: dict = {}
    if uid is not None:
        headers["X-Incus-uid"] = str(uid)
    if gid is not None:
        headers["X-Incus-gid"] = str(gid)
    if mode:
        headers["X-Incus-mode"] = mode
    if file_type:
        headers["X-Incus-type"] = file_type
    return _ok(_get_client().post(f"/1.0/instances/{name}/files", params=params, headers=headers, content=content.encode()))


@_op(incus_write)
def create_instance_template(name: str, template: dict):
    """Create an instance file template."""
    return _ok(_get_client().post(f"/1.0/instances/{name}/metadata/templates", json=template))


@_op(incus_write)
def rebuild_instance(name: str, source: dict):
    """Rebuild an instance from a new image source."""
    return _ok(_get_client().post(f"/1.0/instances/{name}/rebuild", json={"source": source}))


# ── Instance Snapshots ───────────────────────────────────────────────


@_op(incus_write)
def create_snapshot(name: str, snapshot_name: str, stateful: bool = False, project: str | None = None):
    """Create an instance snapshot."""
    body = {"name": snapshot_name, "stateful": stateful}
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().post(f"/1.0/instances/{name}/snapshots", json=body, params=params))


@_op(incus_write)
def update_snapshot(name: str, snapshot: str, expires_at: str | None = None):
    """Update instance snapshot properties."""
    body: dict = {}
    if expires_at is not None:
        body["expires_at"] = expires_at
    return _ok(_get_client().put(f"/1.0/instances/{name}/snapshots/{snapshot}", json=body))


@_op(incus_write)
def rename_snapshot(name: str, snapshot: str, new_name: str):
    """Rename an instance snapshot."""
    return _ok(_get_client().post(f"/1.0/instances/{name}/snapshots/{snapshot}", json={"name": new_name}))


# ── Instance Backups ─────────────────────────────────────────────────


@_op(incus_write)
def create_backup(name: str, backup_name: str | None = None, compression_algorithm: str | None = None,
                  instance_only: bool = False, optimized_storage: bool = False):
    """Create an instance backup."""
    body: dict = {"instance_only": instance_only, "optimized_storage": optimized_storage}
    if backup_name:
        body["name"] = backup_name
    if compression_algorithm:
        body["compression_algorithm"] = compression_algorithm
    return _ok(_get_client().post(f"/1.0/instances/{name}/backups", json=body))


@_op(incus_write)
def rename_backup(name: str, backup: str, new_name: str):
    """Rename an instance backup."""
    return _ok(_get_client().post(f"/1.0/instances/{name}/backups/{backup}", json={"name": new_name}))


# ── Images ───────────────────────────────────────────────────────────


@_op(incus_write)
def create_image(source: dict, public: bool = False, auto_update: bool = False,
                 properties: dict | None = None, project: str | None = None):
    """Create/import an image. source: {"type": "url", "url": "..."} or {"type": "instance", "name": "..."}."""
    body: dict = {"source": source, "public": public, "auto_update": auto_update}
    if properties:
        body["properties"] = properties
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().post("/1.0/images", json=body, params=params))


@_op(incus_write)
def update_image(fingerprint: str, properties: dict | None = None, public: bool | None = None,
                 auto_update: bool | None = None, project: str | None = None):
    """Update image properties (full replace)."""
    body: dict = {}
    if properties is not None:
        body["properties"] = properties
    if public is not None:
        body["public"] = public
    if auto_update is not None:
        body["auto_update"] = auto_update
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/images/{fingerprint}", json=body, params=params))


@_op(incus_write)
def patch_image(fingerprint: str, properties: dict | None = None, public: bool | None = None,
                project: str | None = None):
    """Partially update image properties."""
    body: dict = {}
    if properties is not None:
        body["properties"] = properties
    if public is not None:
        body["public"] = public
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().patch(f"/1.0/images/{fingerprint}", json=body, params=params))


@_op(incus_write)
def refresh_image(fingerprint: str):
    """Refresh an image from its source."""
    return _ok(_get_client().post(f"/1.0/images/{fingerprint}/refresh"))


@_op(incus_write)
def create_image_alias(name: str, target: str, description: str | None = None):
    """Create an image alias."""
    body: dict = {"name": name, "target": target}
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/images/aliases", json=body))


@_op(incus_write)
def update_image_alias(name: str, target: str, description: str | None = None):
    """Update an image alias target."""
    body: dict = {"target": target}
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/images/aliases/{name}", json=body))


@_op(incus_write)
def rename_image_alias(name: str, new_name: str):
    """Rename an image alias."""
    return _ok(_get_client().post(f"/1.0/images/aliases/{name}", json={"name": new_name}))


# ── Networks ─────────────────────────────────────────────────────────


@_op(incus_write)
def create_network(name: str, type: str = "bridge", config: dict | None = None,
                   description: str | None = None, project: str | None = None):
    """Create a network."""
    body: dict = {"name": name, "type": type}
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().post("/1.0/networks", json=body, params=params))


@_op(incus_write)
def update_network(name: str, config: dict | None = None, description: str | None = None,
                   project: str | None = None):
    """Update network configuration (full replace)."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/networks/{name}", json=body, params=params))


@_op(incus_write)
def patch_network(name: str, config: dict | None = None, description: str | None = None,
                  project: str | None = None):
    """Partially update network configuration."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().patch(f"/1.0/networks/{name}", json=body, params=params))


@_op(incus_write)
def rename_network(name: str, new_name: str):
    """Rename a network."""
    return _ok(_get_client().post(f"/1.0/networks/{name}", json={"name": new_name}))


@_op(incus_write)
def create_network_forward(network: str, listen_address: str, config: dict | None = None,
                           ports: list[dict] | None = None):
    """Create a network address forward."""
    body: dict = {"listen_address": listen_address}
    if config:
        body["config"] = config
    if ports:
        body["ports"] = ports
    return _ok(_get_client().post(f"/1.0/networks/{network}/forwards", json=body))


@_op(incus_write)
def update_network_forward(network: str, listen_address: str, config: dict | None = None,
                           ports: list[dict] | None = None):
    """Update a network address forward."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if ports is not None:
        body["ports"] = ports
    return _ok(_get_client().put(f"/1.0/networks/{network}/forwards/{listen_address}", json=body))


@_op(incus_write)
def create_load_balancer(network: str, listen_address: str, config: dict | None = None,
                         backends: list[dict] | None = None, ports: list[dict] | None = None):
    """Create a network load balancer."""
    body: dict = {"listen_address": listen_address}
    if config:
        body["config"] = config
    if backends:
        body["backends"] = backends
    if ports:
        body["ports"] = ports
    return _ok(_get_client().post(f"/1.0/networks/{network}/load-balancers", json=body))


@_op(incus_write)
def update_load_balancer(network: str, listen_address: str, config: dict | None = None,
                         backends: list[dict] | None = None, ports: list[dict] | None = None):
    """Update a network load balancer."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if backends is not None:
        body["backends"] = backends
    if ports is not None:
        body["ports"] = ports
    return _ok(_get_client().put(f"/1.0/networks/{network}/load-balancers/{listen_address}", json=body))


@_op(incus_write)
def create_network_peer(network: str, name: str, target_network: str, target_project: str | None = None,
                        config: dict | None = None):
    """Create a network peer."""
    body: dict = {"name": name, "target_network": target_network}
    if target_project:
        body["target_project"] = target_project
    if config:
        body["config"] = config
    return _ok(_get_client().post(f"/1.0/networks/{network}/peers", json=body))


@_op(incus_write)
def update_network_peer(network: str, peer: str, config: dict | None = None):
    """Update a network peer."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    return _ok(_get_client().put(f"/1.0/networks/{network}/peers/{peer}", json=body))


# ── Network ACLs ─────────────────────────────────────────────────────


@_op(incus_write)
def create_network_acl(name: str, egress: list[dict] | None = None, ingress: list[dict] | None = None,
                       config: dict | None = None, description: str | None = None):
    """Create a network ACL."""
    body: dict = {"name": name}
    if egress:
        body["egress"] = egress
    if ingress:
        body["ingress"] = ingress
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/network-acls", json=body))


@_op(incus_write)
def update_network_acl(name: str, egress: list[dict] | None = None, ingress: list[dict] | None = None,
                       config: dict | None = None, description: str | None = None):
    """Update a network ACL (full replace)."""
    body: dict = {}
    if egress is not None:
        body["egress"] = egress
    if ingress is not None:
        body["ingress"] = ingress
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/network-acls/{name}", json=body))


@_op(incus_write)
def rename_network_acl(name: str, new_name: str):
    """Rename a network ACL."""
    return _ok(_get_client().post(f"/1.0/network-acls/{name}", json={"name": new_name}))


# ── Network Address Sets ─────────────────────────────────────────────


@_op(incus_write)
def create_network_address_set(name: str, addresses: list[str] | None = None,
                               description: str | None = None):
    """Create a network address set."""
    body: dict = {"name": name}
    if addresses:
        body["addresses"] = addresses
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/network-address-sets", json=body))


@_op(incus_write)
def update_network_address_set(name: str, addresses: list[str] | None = None,
                               description: str | None = None):
    """Update a network address set."""
    body: dict = {}
    if addresses is not None:
        body["addresses"] = addresses
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/network-address-sets/{name}", json=body))


@_op(incus_write)
def rename_network_address_set(name: str, new_name: str):
    """Rename a network address set."""
    return _ok(_get_client().post(f"/1.0/network-address-sets/{name}", json={"name": new_name}))


# ── Network Integrations ─────────────────────────────────────────────


@_op(incus_write)
def create_network_integration(name: str, type: str, config: dict | None = None,
                               description: str | None = None):
    """Create a network integration."""
    body: dict = {"name": name, "type": type}
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/network-integrations", json=body))


@_op(incus_write)
def update_network_integration(name: str, config: dict | None = None, description: str | None = None):
    """Update a network integration."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/network-integrations/{name}", json=body))


@_op(incus_write)
def rename_network_integration(name: str, new_name: str):
    """Rename a network integration."""
    return _ok(_get_client().post(f"/1.0/network-integrations/{name}", json={"name": new_name}))


# ── Network Zones ────────────────────────────────────────────────────


@_op(incus_write)
def create_network_zone(name: str, config: dict | None = None, description: str | None = None):
    """Create a network zone."""
    body: dict = {"name": name}
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/network-zones", json=body))


@_op(incus_write)
def update_network_zone(zone: str, config: dict | None = None, description: str | None = None):
    """Update a network zone."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/network-zones/{zone}", json=body))


@_op(incus_write)
def create_zone_record(zone: str, name: str, entries: list[dict] | None = None,
                       config: dict | None = None, description: str | None = None):
    """Create a DNS record in a network zone."""
    body: dict = {"name": name}
    if entries:
        body["entries"] = entries
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    return _ok(_get_client().post(f"/1.0/network-zones/{zone}/records", json=body))


@_op(incus_write)
def update_zone_record(zone: str, name: str, entries: list[dict] | None = None,
                       config: dict | None = None, description: str | None = None):
    """Update a DNS record in a network zone."""
    body: dict = {}
    if entries is not None:
        body["entries"] = entries
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/network-zones/{zone}/records/{name}", json=body))


# ── Storage Pools ────────────────────────────────────────────────────


@_op(incus_write)
def create_storage_pool(name: str, driver: str, config: dict | None = None,
                        description: str | None = None):
    """Create a storage pool."""
    body: dict = {"name": name, "driver": driver}
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/storage-pools", json=body))


@_op(incus_write)
def update_storage_pool(pool: str, config: dict | None = None, description: str | None = None):
    """Update storage pool configuration."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/storage-pools/{pool}", json=body))


# ── Storage Volumes ──────────────────────────────────────────────────


@_op(incus_write)
def create_volume(pool: str, name: str, type: str = "custom", config: dict | None = None,
                  content_type: str | None = None, project: str | None = None):
    """Create a storage volume."""
    body: dict = {"name": name, "type": type}
    if config:
        body["config"] = config
    if content_type:
        body["content_type"] = content_type
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/volumes", json=body, params=params))


@_op(incus_write)
def update_volume(pool: str, type: str, volume: str, config: dict | None = None,
                  description: str | None = None, project: str | None = None):
    """Update storage volume configuration."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}", json=body, params=params))


@_op(incus_write)
def rename_volume(pool: str, type: str, volume: str, new_name: str):
    """Rename/move a storage volume."""
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}", json={"name": new_name}))


@_op(incus_write)
def create_volume_snapshot(pool: str, type: str, volume: str, snapshot_name: str):
    """Create a volume snapshot."""
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots", json={"name": snapshot_name}))


@_op(incus_write)
def update_volume_snapshot(pool: str, type: str, volume: str, snapshot: str,
                           expires_at: str | None = None, description: str | None = None):
    """Update volume snapshot properties."""
    body: dict = {}
    if expires_at is not None:
        body["expires_at"] = expires_at
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}", json=body))


@_op(incus_write)
def rename_volume_snapshot(pool: str, type: str, volume: str, snapshot: str, new_name: str):
    """Rename a volume snapshot."""
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}", json={"name": new_name}))


@_op(incus_write)
def create_volume_backup(pool: str, type: str, volume: str, backup_name: str | None = None,
                         compression_algorithm: str | None = None, volume_only: bool = False,
                         optimized_storage: bool = False):
    """Create a volume backup."""
    body: dict = {"volume_only": volume_only, "optimized_storage": optimized_storage}
    if backup_name:
        body["name"] = backup_name
    if compression_algorithm:
        body["compression_algorithm"] = compression_algorithm
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups", json=body))


@_op(incus_write)
def rename_volume_backup(pool: str, type: str, volume: str, backup: str, new_name: str):
    """Rename a volume backup."""
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups/{backup}", json={"name": new_name}))


# ── Storage Buckets ──────────────────────────────────────────────────


@_op(incus_write)
def create_bucket(pool: str, name: str, config: dict | None = None, description: str | None = None):
    """Create a storage bucket."""
    body: dict = {"name": name}
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/buckets", json=body))


@_op(incus_write)
def update_bucket(pool: str, bucket: str, config: dict | None = None, description: str | None = None):
    """Update storage bucket configuration."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/storage-pools/{pool}/buckets/{bucket}", json=body))


@_op(incus_write)
def create_bucket_key(pool: str, bucket: str, name: str, role: str = "read-only",
                      description: str | None = None):
    """Create a storage bucket access key."""
    body: dict = {"name": name, "role": role}
    if description:
        body["description"] = description
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys", json=body))


@_op(incus_write)
def update_bucket_key(pool: str, bucket: str, key: str, role: str | None = None,
                      description: str | None = None):
    """Update a storage bucket access key."""
    body: dict = {}
    if role is not None:
        body["role"] = role
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys/{key}", json=body))


@_op(incus_write)
def create_bucket_backup(pool: str, bucket: str, backup_name: str | None = None,
                         compression_algorithm: str | None = None):
    """Create a storage bucket backup."""
    body: dict = {}
    if backup_name:
        body["name"] = backup_name
    if compression_algorithm:
        body["compression_algorithm"] = compression_algorithm
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups", json=body))


@_op(incus_write)
def rename_bucket_backup(pool: str, bucket: str, backup: str, new_name: str):
    """Rename a storage bucket backup."""
    return _ok(_get_client().post(f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups/{backup}", json={"name": new_name}))


# ── Profiles ─────────────────────────────────────────────────────────


@_op(incus_write)
def create_profile(name: str, config: dict | None = None, devices: dict | None = None,
                   description: str | None = None, project: str | None = None):
    """Create a profile."""
    body: dict = {"name": name}
    if config:
        body["config"] = config
    if devices:
        body["devices"] = devices
    if description:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().post("/1.0/profiles", json=body, params=params))


@_op(incus_write)
def update_profile(name: str, config: dict | None = None, devices: dict | None = None,
                   description: str | None = None, project: str | None = None):
    """Update a profile (full replace)."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if devices is not None:
        body["devices"] = devices
    if description is not None:
        body["description"] = description
    params = {}
    if project:
        params["project"] = project
    return _ok(_get_client().put(f"/1.0/profiles/{name}", json=body, params=params))


@_op(incus_write)
def rename_profile(name: str, new_name: str):
    """Rename a profile."""
    return _ok(_get_client().post(f"/1.0/profiles/{name}", json={"name": new_name}))


# ── Projects ─────────────────────────────────────────────────────────


@_op(incus_write)
def create_project(name: str, config: dict | None = None, description: str | None = None):
    """Create a project."""
    body: dict = {"name": name}
    if config:
        body["config"] = config
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/projects", json=body))


@_op(incus_write)
def update_project(name: str, config: dict | None = None, description: str | None = None):
    """Update a project (full replace)."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/projects/{name}", json=body))


@_op(incus_write)
def rename_project(name: str, new_name: str):
    """Rename a project."""
    return _ok(_get_client().post(f"/1.0/projects/{name}", json={"name": new_name}))


# ── Cluster ──────────────────────────────────────────────────────────


@_op(incus_write)
def update_cluster(server_name: str | None = None, enabled: bool | None = None,
                   cluster_address: str | None = None):
    """Update cluster configuration."""
    body: dict = {}
    if server_name is not None:
        body["server_name"] = server_name
    if enabled is not None:
        body["enabled"] = enabled
    if cluster_address is not None:
        body["cluster_address"] = cluster_address
    return _ok(_get_client().put("/1.0/cluster", json=body))


@_op(incus_write)
def update_cluster_certificate(cluster_certificate: str, cluster_certificate_key: str):
    """Update the cluster certificate."""
    body = {"cluster_certificate": cluster_certificate, "cluster_certificate_key": cluster_certificate_key}
    return _ok(_get_client().put("/1.0/cluster/certificate", json=body))


@_op(incus_write)
def request_join_token(name: str):
    """Request a cluster join token for a new member."""
    return _ok(_get_client().post("/1.0/cluster/members", json={"server_name": name}))


@_op(incus_write)
def update_cluster_member(name: str, config: dict | None = None, description: str | None = None,
                          groups: list[str] | None = None):
    """Update cluster member configuration."""
    body: dict = {}
    if config is not None:
        body["config"] = config
    if description is not None:
        body["description"] = description
    if groups is not None:
        body["groups"] = groups
    return _ok(_get_client().put(f"/1.0/cluster/members/{name}", json=body))


@_op(incus_write)
def rename_cluster_member(name: str, new_name: str):
    """Rename a cluster member."""
    return _ok(_get_client().post(f"/1.0/cluster/members/{name}", json={"server_name": new_name}))


@_op(incus_write)
def create_cluster_group(name: str, members: list[str] | None = None, description: str | None = None):
    """Create a cluster group."""
    body: dict = {"name": name}
    if members:
        body["members"] = members
    if description:
        body["description"] = description
    return _ok(_get_client().post("/1.0/cluster/groups", json=body))


@_op(incus_write)
def update_cluster_group(name: str, members: list[str] | None = None, description: str | None = None):
    """Update a cluster group."""
    body: dict = {}
    if members is not None:
        body["members"] = members
    if description is not None:
        body["description"] = description
    return _ok(_get_client().put(f"/1.0/cluster/groups/{name}", json=body))


@_op(incus_write)
def rename_cluster_group(name: str, new_name: str):
    """Rename a cluster group."""
    return _ok(_get_client().post(f"/1.0/cluster/groups/{name}", json={"name": new_name}))


# ── Certificates ─────────────────────────────────────────────────────


@_op(incus_write)
def add_certificate(certificate: str, name: str | None = None, type: str = "client",
                    restricted: bool = False, projects: list[str] | None = None):
    """Add a trusted certificate."""
    body: dict = {"certificate": certificate, "type": type, "restricted": restricted}
    if name:
        body["name"] = name
    if projects:
        body["projects"] = projects
    return _ok(_get_client().post("/1.0/certificates", json=body))


@_op(incus_write)
def update_certificate(fingerprint: str, certificate: str | None = None, name: str | None = None,
                       restricted: bool | None = None, projects: list[str] | None = None):
    """Update a trusted certificate."""
    body: dict = {}
    if certificate is not None:
        body["certificate"] = certificate
    if name is not None:
        body["name"] = name
    if restricted is not None:
        body["restricted"] = restricted
    if projects is not None:
        body["projects"] = projects
    return _ok(_get_client().put(f"/1.0/certificates/{fingerprint}", json=body))
