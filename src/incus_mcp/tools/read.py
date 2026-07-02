from __future__ import annotations

import asyncio
import time
from typing import Annotated, Any, cast

from mcp.server.fastmcp import Image
from pydantic import Field

from .. import wait_registry as _wr
from ..client import APIError
from ..registry import ROOT, _UNSET, _op
from ..types import (
    ImageDict,
    InstanceDict,
    NetworkDict,
    ProfileDict,
    ProjectDict,
    SlimImageDict,
    SlimInstanceDict,
    SlimNetworkDict,
    SlimProfileDict,
    SlimProjectDict,
    SlimVolumeDict,
    VolumeDict,
    WaitSnapshotDict,
    WarningDict,
)
from .groups import incus_read
from .helpers import (
    SLIM_IMAGE,
    SLIM_INSTANCE,
    SLIM_NETWORK,
    SLIM_PROFILE,
    SLIM_PROJECT,
    SLIM_VOLUME,
    _ALL_PROJECTS_DESC,
    _API_FILTER_DESC,
    _PROJECT_DESC,
    _REGEX_FILTER_DESC,
    _TAIL_DESC,
    _VOLUME_TYPE_DESC,
    _drain_pending_verify,
    _get_client,
    _qp,
    _slim_list,
    _tail_filter,
    _verify_response,
)

# Type aliases used only in this file. External JSON is cast at the client
# boundary; downstream code sees the declared shape.
_JSON: Any = None  # runtime unused, kept as documentation anchor


# ── Version ──────────────────────────────────────────────────────────


@_op(ROOT)
def incus_version() -> dict[str, Any]:
    """Get the Incus MCP server version and service status."""
    from importlib.metadata import version

    server = cast("dict[str, Any]", _get_client().get("/1.0"))
    env = server.get("environment") or {}
    return {
        "mcp": version("incus-mcp"),
        "server": {
            "environment": env.get("server_name"),
            "api_version": server.get("api_version"),
        },
    }


# ── Server ───────────────────────────────────────────────────────────


@_op(incus_read)
def get_server() -> dict[str, Any]:
    """Get server environment and config."""
    return cast("dict[str, Any]", _get_client().get("/1.0"))


@_op(incus_read)
def get_resources() -> dict[str, Any]:
    """Get system resources: CPU, memory, GPU, storage, network, USB, PCI."""
    return cast("dict[str, Any]", _get_client().get("/1.0/resources"))


@_op(incus_read)
def get_metrics(
    tail: Annotated[int, Field(description=_TAIL_DESC)] = 0,
    filter: Annotated[str | None, Field(description=_REGEX_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> str:
    """Get Prometheus metrics."""
    text = _get_client().get("/1.0/metrics")
    return _tail_filter(text, tail, None if filter is _UNSET else filter)


@_op(incus_read)
def get_metadata_config() -> dict[str, Any]:
    """Get metadata configuration documentation."""
    return cast("dict[str, Any]", _get_client().get("/1.0/metadata/configuration"))


# ── Instances ────────────────────────────────────────────────────────


@_op(incus_read)
def list_instances(
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
    filter: Annotated[str | None, Field(description=_API_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
    all_projects: Annotated[bool, Field(description=_ALL_PROJECTS_DESC)] = False,
) -> list[SlimInstanceDict]:
    """List instances (slim: name, status, type, architecture, location, project, created_at)."""
    data = _get_client().get(
        "/1.0/instances",
        params=_qp(
            project=project,
            filter=filter,
            all_projects=all_projects,
            recursion=1,
        ),
    )
    return cast("list[SlimInstanceDict]", _slim_list(data, SLIM_INSTANCE))


@_op(incus_read)
def show_instance(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> InstanceDict:
    """Get full instance details."""
    return cast(
        InstanceDict,
        _get_client().get(f"/1.0/instances/{name}", params=_qp(project=project)),
    )


@_op(incus_read)
def get_instance_state(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> dict[str, Any]:
    """Get instance state: CPU, memory, disk, network usage."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/instances/{name}/state", params=_qp(project=project)
        ),
    )


@_op(incus_read)
def get_instance_access(name: str) -> dict[str, Any]:
    """Get instance access information."""
    return cast("dict[str, Any]", _get_client().get(f"/1.0/instances/{name}/access"))


@_op(incus_read)
def list_instance_logs(name: str) -> list[str]:
    """List instance log files."""
    return cast("list[str]", _get_client().get(f"/1.0/instances/{name}/logs"))


@_op(incus_read)
def get_instance_log(
    name: str,
    filename: str,
    tail: Annotated[int, Field(description=_TAIL_DESC)] = 100,
    filter: Annotated[str | None, Field(description=_REGEX_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> str:
    """Get a specific instance log file."""
    text = _get_client().get(f"/1.0/instances/{name}/logs/{filename}")
    return _tail_filter(text, tail, None if filter is _UNSET else filter)


@_op(incus_read)
def list_exec_outputs(name: str) -> list[str]:
    """List exec output files for an instance."""
    return cast(
        "list[str]", _get_client().get(f"/1.0/instances/{name}/logs/exec-output")
    )


@_op(incus_read)
def get_exec_output(
    name: str,
    filename: str,
    tail: Annotated[int, Field(description=_TAIL_DESC)] = 100,
    filter: Annotated[str | None, Field(description=_REGEX_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> str:
    """Get a specific exec output file."""
    text = _get_client().get(f"/1.0/instances/{name}/logs/exec-output/{filename}")
    return _tail_filter(text, tail, None if filter is _UNSET else filter)


@_op(incus_read)
def get_console_output(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
    tail: Annotated[int, Field(description=_TAIL_DESC)] = 100,
    filter: Annotated[str | None, Field(description=_REGEX_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> str:
    """Get instance console output."""
    text = _get_client().get(
        f"/1.0/instances/{name}/console", params=_qp(project=project)
    )
    return _tail_filter(text, tail, None if filter is _UNSET else filter)


@_op(incus_read)
def get_console_screenshot(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> Image:
    """Get a PNG screenshot of the VM's VGA console."""
    data = _get_client().get_raw(
        f"/1.0/instances/{name}/console", params=_qp(project=project, type="vga")
    )
    return Image(data=data, format="png")


@_op(incus_read)
def get_instance_file(
    name: str,
    path: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> Any:
    """Get a file from an instance (raw text or directory listing dict)."""
    return _get_client().get(
        f"/1.0/instances/{name}/files", params=_qp(project=project, path=path)
    )


@_op(incus_read)
def get_instance_metadata(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> dict[str, Any]:
    """Get instance image metadata."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/instances/{name}/metadata", params=_qp(project=project)
        ),
    )


@_op(incus_read)
def list_instance_templates(name: str) -> list[str]:
    """List instance file templates."""
    return cast(
        "list[str]",
        _get_client().get(f"/1.0/instances/{name}/metadata/templates"),
    )


# ── Instance Snapshots ───────────────────────────────────────────────


@_op(incus_read)
def list_snapshots(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[dict[str, Any]]:
    """List instance snapshots."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/instances/{name}/snapshots",
            params=_qp(project=project, recursion=1),
        ),
    )


@_op(incus_read)
def show_snapshot(name: str, snapshot: str) -> dict[str, Any]:
    """Get snapshot details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/instances/{name}/snapshots/{snapshot}"),
    )


# ── Instance Backups ─────────────────────────────────────────────────


@_op(incus_read)
def list_backups(name: str) -> list[dict[str, Any]]:
    """List instance backups."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(f"/1.0/instances/{name}/backups", params=_qp(recursion=1)),
    )


@_op(incus_read)
def show_backup(name: str, backup: str) -> dict[str, Any]:
    """Get backup details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/instances/{name}/backups/{backup}"),
    )


# ── Images ───────────────────────────────────────────────────────────


@_op(incus_read)
def list_images(
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
    filter: Annotated[str | None, Field(description=_API_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
    all_projects: Annotated[bool, Field(description=_ALL_PROJECTS_DESC)] = False,
) -> list[SlimImageDict]:
    """List images (slim: fingerprint, type, architecture, size, created_at, description)."""
    data = _get_client().get(
        "/1.0/images",
        params=_qp(
            project=project,
            filter=filter,
            all_projects=all_projects,
            recursion=1,
        ),
    )
    return cast("list[SlimImageDict]", _slim_list(data, SLIM_IMAGE))


@_op(incus_read)
def show_image(
    fingerprint: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> ImageDict:
    """Get full image details."""
    return cast(
        ImageDict,
        _get_client().get(
            f"/1.0/images/{fingerprint}", params=_qp(project=project)
        ),
    )


@_op(incus_read)
def list_image_aliases(
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[dict[str, Any]]:
    """List image aliases."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            "/1.0/images/aliases", params=_qp(project=project, recursion=1)
        ),
    )


@_op(incus_read)
def show_image_alias(name: str) -> dict[str, Any]:
    """Get image alias details."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/images/aliases/{name}")
    )


# ── Networks ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_networks(
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
    filter: Annotated[str | None, Field(description=_API_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[SlimNetworkDict]:
    """List networks (slim: name, type, managed, status)."""
    data = _get_client().get(
        "/1.0/networks", params=_qp(project=project, filter=filter, recursion=1)
    )
    return cast("list[SlimNetworkDict]", _slim_list(data, SLIM_NETWORK))


@_op(incus_read)
def show_network(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> NetworkDict:
    """Get full network details."""
    return cast(
        NetworkDict,
        _get_client().get(f"/1.0/networks/{name}", params=_qp(project=project)),
    )


@_op(incus_read)
def get_network_state(name: str) -> dict[str, Any]:
    """Get network state."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/networks/{name}/state")
    )


@_op(incus_read)
def get_network_leases(name: str) -> list[dict[str, Any]]:
    """Get network DHCP leases."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(f"/1.0/networks/{name}/leases"),
    )


@_op(incus_read)
def list_network_forwards(network: str) -> list[dict[str, Any]]:
    """List network address forwards."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/networks/{network}/forwards", params=_qp(recursion=1)
        ),
    )


@_op(incus_read)
def show_network_forward(network: str, listen_address: str) -> dict[str, Any]:
    """Get network forward details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/networks/{network}/forwards/{listen_address}"),
    )


@_op(incus_read)
def list_load_balancers(network: str) -> list[dict[str, Any]]:
    """List network load balancers."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/networks/{network}/load-balancers", params=_qp(recursion=1)
        ),
    )


@_op(incus_read)
def show_load_balancer(network: str, listen_address: str) -> dict[str, Any]:
    """Get load balancer details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/networks/{network}/load-balancers/{listen_address}"
        ),
    )


@_op(incus_read)
def get_load_balancer_state(network: str, listen_address: str) -> dict[str, Any]:
    """Get load balancer state."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/networks/{network}/load-balancers/{listen_address}/state"
        ),
    )


@_op(incus_read)
def list_network_peers(network: str) -> list[dict[str, Any]]:
    """List network peers."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/networks/{network}/peers", params=_qp(recursion=1)
        ),
    )


@_op(incus_read)
def show_network_peer(network: str, peer: str) -> dict[str, Any]:
    """Get network peer details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/networks/{network}/peers/{peer}"),
    )


# ── Network ACLs ─────────────────────────────────────────────────────


@_op(incus_read)
def list_network_acls(
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[dict[str, Any]]:
    """List network ACLs."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            "/1.0/network-acls", params=_qp(project=project, recursion=1)
        ),
    )


@_op(incus_read)
def show_network_acl(name: str) -> dict[str, Any]:
    """Get network ACL details."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/network-acls/{name}")
    )


@_op(incus_read)
def get_network_acl_log(
    name: str,
    tail: Annotated[int, Field(description=_TAIL_DESC)] = 100,
    filter: Annotated[str | None, Field(description=_REGEX_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> str:
    """Get network ACL log."""
    text = _get_client().get(f"/1.0/network-acls/{name}/log")
    return _tail_filter(text, tail, None if filter is _UNSET else filter)


# ── Network Address Sets ─────────────────────────────────────────────


@_op(incus_read)
def list_network_address_sets() -> list[dict[str, Any]]:
    """List network address sets."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get("/1.0/network-address-sets", params=_qp(recursion=1)),
    )


@_op(incus_read)
def show_network_address_set(name: str) -> dict[str, Any]:
    """Get network address set details."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/network-address-sets/{name}")
    )


# ── Network Allocations ──────────────────────────────────────────────


@_op(incus_read)
def get_network_allocations() -> list[dict[str, Any]]:
    """Get network allocations."""
    return cast(
        "list[dict[str, Any]]", _get_client().get("/1.0/network-allocations")
    )


# ── Network Integrations ─────────────────────────────────────────────


@_op(incus_read)
def list_network_integrations() -> list[dict[str, Any]]:
    """List network integrations."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            "/1.0/network-integrations", params=_qp(recursion=1)
        ),
    )


@_op(incus_read)
def show_network_integration(name: str) -> dict[str, Any]:
    """Get network integration details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/network-integrations/{name}"),
    )


# ── Network Zones ────────────────────────────────────────────────────


@_op(incus_read)
def list_network_zones() -> list[dict[str, Any]]:
    """List network zones."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get("/1.0/network-zones", params=_qp(recursion=1)),
    )


@_op(incus_read)
def show_network_zone(zone: str) -> dict[str, Any]:
    """Get network zone details."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/network-zones/{zone}")
    )


@_op(incus_read)
def list_zone_records(zone: str) -> list[dict[str, Any]]:
    """List DNS records in a network zone."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/network-zones/{zone}/records", params=_qp(recursion=1)
        ),
    )


@_op(incus_read)
def show_zone_record(zone: str, name: str) -> dict[str, Any]:
    """Get DNS record details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/network-zones/{zone}/records/{name}"),
    )


# ── Storage Pools ────────────────────────────────────────────────────


@_op(incus_read)
def list_storage_pools(
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[dict[str, Any]]:
    """List storage pools."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            "/1.0/storage-pools", params=_qp(project=project, recursion=1)
        ),
    )


@_op(incus_read)
def show_storage_pool(
    pool: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> dict[str, Any]:
    """Get storage pool details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}", params=_qp(project=project)
        ),
    )


@_op(incus_read)
def get_pool_resources(pool: str) -> dict[str, Any]:
    """Get storage pool resource usage."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/storage-pools/{pool}/resources"),
    )


# ── Storage Volumes ──────────────────────────────────────────────────


@_op(incus_read)
def list_volumes(
    pool: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
    type: Annotated[str | None, Field(description=_VOLUME_TYPE_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[SlimVolumeDict]:
    """List storage volumes (slim: name, type, content_type, location)."""
    path = f"/1.0/storage-pools/{pool}/volumes"
    if type is not _UNSET and type:
        path = f"{path}/{type}"
    data = _get_client().get(path, params=_qp(project=project, recursion=1))
    return cast("list[SlimVolumeDict]", _slim_list(data, SLIM_VOLUME))


@_op(incus_read)
def show_volume(
    pool: str,
    type: str,
    volume: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> VolumeDict:
    """Get full volume details."""
    return cast(
        VolumeDict,
        _get_client().get(
            f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}",
            params=_qp(project=project),
        ),
    )


@_op(incus_read)
def get_volume_state(pool: str, type: str, volume: str) -> dict[str, Any]:
    """Get volume state."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/state"
        ),
    )


@_op(incus_read)
def list_volume_snapshots(
    pool: str, type: str, volume: str
) -> list[dict[str, Any]]:
    """List volume snapshots."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots",
            params=_qp(recursion=1),
        ),
    )


@_op(incus_read)
def show_volume_snapshot(
    pool: str, type: str, volume: str, snapshot: str
) -> dict[str, Any]:
    """Get volume snapshot details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}"
        ),
    )


@_op(incus_read)
def list_volume_backups(
    pool: str, type: str, volume: str
) -> list[dict[str, Any]]:
    """List volume backups."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups",
            params=_qp(recursion=1),
        ),
    )


@_op(incus_read)
def show_volume_backup(
    pool: str, type: str, volume: str, backup: str
) -> dict[str, Any]:
    """Get volume backup details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups/{backup}"
        ),
    )


# ── Storage Buckets ──────────────────────────────────────────────────


@_op(incus_read)
def list_buckets(pool: str) -> list[dict[str, Any]]:
    """List storage buckets."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/buckets", params=_qp(recursion=1)
        ),
    )


@_op(incus_read)
def show_bucket(pool: str, bucket: str) -> dict[str, Any]:
    """Get storage bucket details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(f"/1.0/storage-pools/{pool}/buckets/{bucket}"),
    )


@_op(incus_read)
def list_bucket_keys(pool: str, bucket: str) -> list[dict[str, Any]]:
    """List storage bucket keys."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys",
            params=_qp(recursion=1),
        ),
    )


@_op(incus_read)
def show_bucket_key(pool: str, bucket: str, key: str) -> dict[str, Any]:
    """Get storage bucket key details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys/{key}"
        ),
    )


@_op(incus_read)
def list_bucket_backups(pool: str, bucket: str) -> list[dict[str, Any]]:
    """List storage bucket backups."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups",
            params=_qp(recursion=1),
        ),
    )


@_op(incus_read)
def show_bucket_backup(pool: str, bucket: str, backup: str) -> dict[str, Any]:
    """Get storage bucket backup details."""
    return cast(
        "dict[str, Any]",
        _get_client().get(
            f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups/{backup}"
        ),
    )


# ── Profiles ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_profiles(
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[SlimProfileDict]:
    """List profiles (slim: name, description)."""
    data = _get_client().get(
        "/1.0/profiles", params=_qp(project=project, recursion=1)
    )
    return cast("list[SlimProfileDict]", _slim_list(data, SLIM_PROFILE))


@_op(incus_read)
def show_profile(
    name: str,
    project: Annotated[str | None, Field(description=_PROJECT_DESC)] = cast(
        str | None, _UNSET
    ),
) -> ProfileDict:
    """Get full profile details."""
    return cast(
        ProfileDict,
        _get_client().get(f"/1.0/profiles/{name}", params=_qp(project=project)),
    )


# ── Projects ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_projects(
    filter: Annotated[str | None, Field(description=_API_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[SlimProjectDict]:
    """List projects (slim: name, description)."""
    data = _get_client().get(
        "/1.0/projects", params=_qp(filter=filter, recursion=1)
    )
    return cast("list[SlimProjectDict]", _slim_list(data, SLIM_PROJECT))


@_op(incus_read)
def show_project(name: str) -> ProjectDict:
    """Get full project details."""
    return cast(ProjectDict, _get_client().get(f"/1.0/projects/{name}"))


@_op(incus_read)
def get_project_access(name: str) -> dict[str, Any]:
    """Get project access information."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/projects/{name}/access")
    )


@_op(incus_read)
def get_project_state(name: str) -> dict[str, Any]:
    """Get project resource usage."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/projects/{name}/state")
    )


# ── Cluster ──────────────────────────────────────────────────────────


@_op(incus_read)
def get_cluster() -> dict[str, Any]:
    """Get cluster information."""
    return cast("dict[str, Any]", _get_client().get("/1.0/cluster"))


@_op(incus_read)
def list_cluster_members(
    filter: Annotated[str | None, Field(description=_API_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[dict[str, Any]]:
    """List cluster members."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            "/1.0/cluster/members", params=_qp(filter=filter, recursion=1)
        ),
    )


@_op(incus_read)
def show_cluster_member(name: str) -> dict[str, Any]:
    """Get cluster member details."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/cluster/members/{name}")
    )


@_op(incus_read)
def get_cluster_member_state(name: str) -> dict[str, Any]:
    """Get cluster member state."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/cluster/members/{name}/state")
    )


@_op(incus_read)
def list_cluster_groups() -> list[dict[str, Any]]:
    """List cluster groups."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get("/1.0/cluster/groups", params=_qp(recursion=1)),
    )


@_op(incus_read)
def show_cluster_group(name: str) -> dict[str, Any]:
    """Get cluster group details."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/cluster/groups/{name}")
    )


# ── Certificates ─────────────────────────────────────────────────────


@_op(incus_read)
def list_certificates(
    filter: Annotated[str | None, Field(description=_API_FILTER_DESC)] = cast(
        str | None, _UNSET
    ),
) -> list[dict[str, Any]]:
    """List trusted certificates."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get(
            "/1.0/certificates", params=_qp(filter=filter, recursion=1)
        ),
    )


@_op(incus_read)
def show_certificate(fingerprint: str) -> dict[str, Any]:
    """Get certificate details."""
    return cast(
        "dict[str, Any]", _get_client().get(f"/1.0/certificates/{fingerprint}")
    )


# ── Operations ───────────────────────────────────────────────────────


@_op(incus_read)
def list_operations() -> list[dict[str, Any]]:
    """List background operations."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get("/1.0/operations", params=_qp(recursion=1)),
    )


@_op(incus_read)
def show_operation(id: str) -> dict[str, Any]:
    """Get operation details."""
    return cast("dict[str, Any]", _get_client().get(f"/1.0/operations/{id}"))


@_op(incus_read)
def wait_operation(id: str) -> dict[str, Any]:
    """Wait for an operation to complete via Incus's server-side long-poll.

    Blocks the FastMCP event loop until Incus responds. One-shot short waits
    only; prefer OperationWaitStart for slow operations. On terminal success
    (status_code == 200), drains any pending-verify entry for `id` and raises
    ValueError if the target GET reveals a silent-drop of a sent config key.
    """
    result = _get_client().get(f"/1.0/operations/{id}/wait")
    if isinstance(result, dict) and result.get("status_code") == 200:
        entry = _drain_pending_verify(id)
        if entry is not None:
            sent, target_path, target_qp = entry
            target = _get_client().get(target_path, params=target_qp or None)
            _verify_response(sent, target)
    return cast("dict[str, Any]", result)


# ── Operation waiters (non-blocking) ─────────────────────────────────


async def _poll(
    handle: _wr.WaitHandle,
    interval: float,
    timeout: float,
    max_poll_failures: int,
    max_lifetime: float,
) -> None:
    """Background poll loop. Sole writer to the handle's mutable state."""
    op_path = f"/1.0/operations/{handle.operation_id}"
    consecutive_failures = 0
    while True:
        elapsed = time.time() - handle.started_at
        if elapsed > max_lifetime:
            handle.mark_timed_out(f"max_lifetime {max_lifetime}s exceeded")
            return
        if elapsed > timeout:
            handle.mark_timed_out(f"timeout {timeout}s exceeded")
            return
        try:
            payload = await asyncio.to_thread(_get_client().get, op_path)
        except APIError as exc:
            if 400 <= exc.status < 500 and exc.status != 429:
                handle.record_poll_failure(str(exc))
                handle.mark_terminated(err=str(exc))
                return
            consecutive_failures += 1
            handle.record_poll_failure(str(exc))
            if consecutive_failures > max_poll_failures:
                handle.mark_terminated(
                    err=f"{consecutive_failures} consecutive poll failures"
                )
                return
            await asyncio.sleep(interval)
            continue
        except Exception as exc:
            consecutive_failures += 1
            handle.record_poll_failure(str(exc))
            if consecutive_failures > max_poll_failures:
                handle.mark_terminated(
                    err=f"{consecutive_failures} consecutive poll failures"
                )
                return
            await asyncio.sleep(interval)
            continue

        consecutive_failures = 0
        handle.polls += 1
        handle.last_payload = payload
        if isinstance(payload, dict):
            handle.record_transition(
                payload.get("status"), payload.get("status_code")
            )
            code = payload.get("status_code")
            if isinstance(code, int) and code in _wr.TERMINAL_STATUS_CODES:
                if code == 200:
                    await _run_drain(handle)
                handle.mark_terminated()
                return
        await asyncio.sleep(interval)


async def _run_drain(handle: _wr.WaitHandle) -> None:
    """Fetch target resource and verify sent-vs-returned; store any drop on the handle."""
    entry = _drain_pending_verify(handle.operation_id)
    if entry is None:
        return
    sent, target_path, target_qp = entry
    try:
        target = await asyncio.to_thread(
            _get_client().get, target_path, params=target_qp or None,
        )
        _verify_response(sent, target)
    except ValueError as exc:
        handle.verify_error = str(exc)
    except Exception as exc:
        handle.enrichment_error = str(exc)


@_op(incus_read)
async def operation_wait_start(
    operation_id: Annotated[
        str,
        Field(
            description=(
                "UUID of the Incus operation to wait for "
                "(from an async POST's response)."
            ),
        ),
    ],
    timeout: Annotated[
        float, Field(description="Seconds to poll before timing out. Default 600.")
    ] = 600,
    interval: Annotated[
        float, Field(description="Seconds between polls. Default 5.")
    ] = 5,
    max_poll_failures: Annotated[
        int,
        Field(
            description=(
                "Consecutive transient failures tolerated before giving up. "
                "Default 3."
            ),
        ),
    ] = 3,
    max_lifetime: Annotated[
        float,
        Field(
            description=(
                "Absolute lifetime cap on the background task (0 = off). "
                "Default 7200 (2h)."
            ),
        ),
    ] = 7200,
) -> WaitSnapshotDict:
    """Start a non-blocking wait on an Incus operation.

    Runs one inline probe first (bad UUID / no access surfaces immediately as
    APIError). If already terminal, drains pending-verify synchronously and
    returns the snapshot without spawning a task. Otherwise spawns a
    background poll task and returns the current snapshot immediately; use
    OperationWaitPoll to await completion, OperationWaitCancel to stop.
    Verify-on-completion is best-effort and only applies within this MCP
    process lifetime that ran the write.
    """
    if interval <= 0:
        raise ValueError(f"interval must be > 0, got {interval}")
    if max_poll_failures < 1:
        raise ValueError(
            f"max_poll_failures must be >= 1, got {max_poll_failures}"
        )

    payload = await asyncio.to_thread(
        _get_client().get, f"/1.0/operations/{operation_id}",
    )
    handle = _wr.create_handle(operation_id, {
        "timeout": float(timeout),
        "interval": float(interval),
        "max_poll_failures": float(max_poll_failures),
        "max_lifetime": float(max_lifetime),
    })
    handle.polls = 1
    handle.last_payload = payload
    if isinstance(payload, dict):
        handle.record_transition(payload.get("status"), payload.get("status_code"))
        code = payload.get("status_code")
        if isinstance(code, int) and code in _wr.TERMINAL_STATUS_CODES:
            if code == 200:
                await _run_drain(handle)
            handle.mark_terminated()
            return handle.snapshot()

    handle.task = asyncio.create_task(
        _poll(handle, interval, timeout, max_poll_failures, max_lifetime),
    )
    return handle.snapshot()


@_op(incus_read)
async def operation_wait_poll(
    wait_id: Annotated[
        str, Field(description="Wait handle ID returned by OperationWaitStart.")
    ],
    max_block: Annotated[
        float,
        Field(
            description=(
                "Seconds to await the completion event before returning "
                "current snapshot. 0 = snapshot now. Default 0."
            ),
        ),
    ] = 0,
) -> WaitSnapshotDict:
    """Return the current snapshot for a wait handle, optionally blocking up to `max_block`s."""
    handle = _wr.get_handle(wait_id)
    if handle is None:
        raise ValueError(f"Unknown wait_id {wait_id!r}")
    if max_block > 0 and not handle.terminated and not handle.timed_out:
        try:
            await asyncio.wait_for(handle.done_event.wait(), max_block)
        except asyncio.TimeoutError:
            pass
    return handle.snapshot()


@_op(incus_read)
async def operation_wait_cancel(
    wait_id: Annotated[
        str,
        Field(
            description=(
                "Wait handle ID. Cancels the local polling task; the Incus "
                "operation itself is unaffected. Use CancelOperation "
                "(incus_delete) to cancel the operation on the server."
            ),
        ),
    ],
) -> WaitSnapshotDict:
    """Cancel the local polling task for a wait handle. Idempotent.

    Cancelling the wait does NOT cancel the target operation; use
    CancelOperation (incus_delete) to cancel the operation server-side.
    Cancelling also does NOT run pending-verify; the entry stays until TTL.
    """
    handle = _wr.get_handle(wait_id)
    if handle is None:
        raise ValueError(f"Unknown wait_id {wait_id!r}")
    if handle.task is not None and not handle.task.done():
        handle.task.cancel()
    return handle.snapshot()


@_op(incus_read)
async def waits_list() -> list[WaitSnapshotDict]:
    """List all in-flight and recently-terminal waits. Reaps expired opportunistically."""
    _wr.reap_expired()
    return [h.snapshot() for h in _wr.list_handles()]


# ── Warnings ─────────────────────────────────────────────────────────


@_op(incus_read)
def list_warnings() -> list[dict[str, Any]]:
    """List warnings."""
    return cast(
        "list[dict[str, Any]]",
        _get_client().get("/1.0/warnings", params=_qp(recursion=1)),
    )


@_op(incus_read)
def show_warning(uuid: str) -> WarningDict:
    """Get warning details."""
    return cast(WarningDict, _get_client().get(f"/1.0/warnings/{uuid}"))
