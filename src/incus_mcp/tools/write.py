from __future__ import annotations

from typing import Annotated, Any, cast

from pydantic import Field

from ..registry import _UNSET, _op
from ..types import OperationDict
from .groups import incus_write
from .helpers import (
    _CONFIG_DESC,
    _DESCRIPTION_DESC,
    _DEVICES_DESC,
    _PROFILES_DESC,
    _PROJECT_DESC,
    _SOURCE_IMAGE_DESC,
    _SOURCE_INSTANCE_DESC,
    _STATEFUL_DESC,
    _TARGET_DESC,
    _get_client,
    _ok,
    _qp,
    _register_pending_verify,
    _verify_response,
)

# ── Common Field-annotated type aliases ──────────────────────────────
# Every optional-nullable body param that carries the same wording lives
# here so annotations across 60+ signatures stay consistent.

_ProjectAnn = Annotated[str | None, Field(description=_PROJECT_DESC)]
_DescriptionAnn = Annotated[str | None, Field(description=_DESCRIPTION_DESC)]
_TargetAnn = Annotated[str | None, Field(description=_TARGET_DESC)]
_ConfigAnn = Annotated[dict[str, Any] | None, Field(description=_CONFIG_DESC)]
_DevicesAnn = Annotated[dict[str, Any] | None, Field(description=_DEVICES_DESC)]
_ProfilesAnn = Annotated[list[str] | None, Field(description=_PROFILES_DESC)]

_UNSET_STR = cast(str | None, _UNSET)
_UNSET_DICT = cast("dict[str, Any] | None", _UNSET)
_UNSET_LIST_STR = cast(list[str] | None, _UNSET)
_UNSET_LIST_DICT = cast(list[dict[str, Any]] | None, _UNSET)
_UNSET_BOOL = cast(bool | None, _UNSET)
_UNSET_INT = cast(int | None, _UNSET)


# ── Instances ────────────────────────────────────────────────────────


@_op(incus_write)
def create_instance(
    name: str,
    source: Annotated[dict[str, Any], Field(description=_SOURCE_INSTANCE_DESC)],
    type: Annotated[
        str,
        Field(description="'container' (LXC) or 'virtual-machine' (VM)."),
    ] = "container",
    project: _ProjectAnn = _UNSET_STR,
    profiles: _ProfilesAnn = _UNSET_LIST_STR,
    config: _ConfigAnn = _UNSET_DICT,
    devices: _DevicesAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    target: _TargetAnn = _UNSET_STR,
) -> OperationDict:
    """Create a new instance. Returns an async operation."""
    body: dict[str, Any] = {"name": name, "source": source, "type": type}
    if profiles is not _UNSET:
        body["profiles"] = profiles
    if config is not _UNSET:
        body["config"] = config
    if devices is not _UNSET:
        body["devices"] = devices
    if description is not _UNSET:
        body["description"] = description
    qp = _qp(project=project, target=target)
    result = _get_client().post("/1.0/instances", json=body, params=qp)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/instances/{name}", qp)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_instance(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    devices: _DevicesAnn = _UNSET_DICT,
    profiles: _ProfilesAnn = _UNSET_LIST_STR,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> OperationDict:
    """Update instance configuration (full replace). Use PatchInstance for partial update."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if devices is not _UNSET:
        body["devices"] = devices
    if profiles is not _UNSET:
        body["profiles"] = profiles
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/instances/{name}", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def patch_instance(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    devices: _DevicesAnn = _UNSET_DICT,
    profiles: _ProfilesAnn = _UNSET_LIST_STR,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Partially update instance configuration (merge-style)."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if devices is not _UNSET:
        body["devices"] = devices
    if profiles is not _UNSET:
        body["profiles"] = profiles
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().patch(
        f"/1.0/instances/{name}", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_instance(name: str, new_name: str) -> OperationDict:
    """Rename an instance (also used for move/migrate). Async."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(f"/1.0/instances/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/instances/{new_name}", {})
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_instance_metadata(
    name: str,
    metadata: Annotated[dict[str, Any],
        Field(description="Instance image metadata dict (architecture, creation_date, properties, ...)."),
    ],
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update instance image metadata."""
    result = _get_client().put(
        f"/1.0/instances/{name}/metadata", json=metadata, params=_qp(project=project),
    )
    _verify_response(metadata, result)
    return _ok(result)


@_op(incus_write)
def upload_instance_file(
    name: str,
    path: Annotated[
        str,
        Field(description="Absolute destination path inside the instance."),
    ],
    content: Annotated[
        str,
        Field(description="File body as text; sent as the raw request body."),
    ],
    project: _ProjectAnn = _UNSET_STR,
    uid: Annotated[int | None, Field(description="Owning uid (X-Incus-uid header).")] = _UNSET_INT,
    gid: Annotated[int | None, Field(description="Owning gid (X-Incus-gid header).")] = _UNSET_INT,
    mode: Annotated[
        str | None,
        Field(description="Octal mode string, e.g. '0644' (X-Incus-mode header)."),
    ] = _UNSET_STR,
    file_type: Annotated[
        str | None,
        Field(description="'file' or 'directory' (X-Incus-type header)."),
    ] = _UNSET_STR,
) -> dict[str, Any]:
    """Upload a file to an instance. Verify skipped: body is raw content, not JSON."""
    headers: dict[str, str] = {}
    if uid is not _UNSET and uid is not None:
        headers["X-Incus-uid"] = str(uid)
    if gid is not _UNSET and gid is not None:
        headers["X-Incus-gid"] = str(gid)
    if mode is not _UNSET and mode is not None and mode != "":
        headers["X-Incus-mode"] = str(mode)
    if file_type is not _UNSET and file_type is not None and file_type != "":
        headers["X-Incus-type"] = str(file_type)
    return _ok(_get_client().post(
        f"/1.0/instances/{name}/files",
        params=_qp(project=project, path=path),
        headers=headers,
        content=content.encode(),
    ))


@_op(incus_write)
def create_instance_template(
    name: str,
    template: Annotated[dict[str, Any],
        Field(description="Template spec (see Incus API for schema)."),
    ],
) -> dict[str, Any]:
    """Create an instance file template."""
    result = _get_client().post(
        f"/1.0/instances/{name}/metadata/templates", json=template,
    )
    _verify_response(template, result)
    return _ok(result)


@_op(incus_write)
def rebuild_instance(
    name: str,
    source: Annotated[dict[str, Any], Field(description=_SOURCE_INSTANCE_DESC)],
    project: _ProjectAnn = _UNSET_STR,
) -> OperationDict:
    """Rebuild an instance from a new image source. Async."""
    body: dict[str, Any] = {"source": source}
    qp = _qp(project=project)
    result = _get_client().post(
        f"/1.0/instances/{name}/rebuild", json=body, params=qp,
    )
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/instances/{name}", qp)
    return cast("OperationDict", _ok(result))


# ── Instance Snapshots ───────────────────────────────────────────────


@_op(incus_write)
def create_snapshot(
    name: str,
    snapshot_name: str,
    stateful: Annotated[bool, Field(description=_STATEFUL_DESC)] = False,
    project: _ProjectAnn = _UNSET_STR,
) -> OperationDict:
    """Create an instance snapshot. Async."""
    body: dict[str, Any] = {"name": snapshot_name, "stateful": stateful}
    qp = _qp(project=project)
    result = _get_client().post(
        f"/1.0/instances/{name}/snapshots", json=body, params=qp,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result, body, f"/1.0/instances/{name}/snapshots/{snapshot_name}", qp,
    )
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_snapshot(
    name: str,
    snapshot: str,
    expires_at: Annotated[
        str | None,
        Field(description="Expiration timestamp (RFC3339, e.g. '2026-12-31T00:00:00Z')."),
    ] = _UNSET_STR,
) -> OperationDict:
    """Update instance snapshot properties."""
    body: dict[str, Any] = {}
    if expires_at is not _UNSET:
        body["expires_at"] = expires_at
    result = _get_client().put(
        f"/1.0/instances/{name}/snapshots/{snapshot}", json=body,
    )
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def rename_snapshot(name: str, snapshot: str, new_name: str) -> OperationDict:
    """Rename an instance snapshot. Async."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/instances/{name}/snapshots/{snapshot}", json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result, body, f"/1.0/instances/{name}/snapshots/{new_name}", {},
    )
    return cast("OperationDict", _ok(result))


# ── Instance Backups ─────────────────────────────────────────────────


@_op(incus_write)
def create_backup(
    name: str,
    backup_name: Annotated[
        str | None,
        Field(description="Backup name (auto-generated when omitted)."),
    ] = _UNSET_STR,
    compression_algorithm: Annotated[
        str | None,
        Field(description="Compression algorithm (e.g. 'gzip', 'lzma', 'zstd')."),
    ] = _UNSET_STR,
    instance_only: Annotated[
        bool, Field(description="Exclude related snapshots from the backup."),
    ] = False,
    optimized_storage: Annotated[
        bool,
        Field(description="Use storage-driver-specific format (re-importable only to same driver)."),
    ] = False,
) -> OperationDict:
    """Create an instance backup. Async. Register skipped when backup_name auto-generated."""
    body: dict[str, Any] = {
        "instance_only": instance_only,
        "optimized_storage": optimized_storage,
    }
    if backup_name is not _UNSET and backup_name:
        body["name"] = backup_name
    if compression_algorithm is not _UNSET and compression_algorithm:
        body["compression_algorithm"] = compression_algorithm
    result = _get_client().post(f"/1.0/instances/{name}/backups", json=body)
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def rename_backup(name: str, backup: str, new_name: str) -> OperationDict:
    """Rename an instance backup. Async."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/instances/{name}/backups/{backup}", json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result, body, f"/1.0/instances/{name}/backups/{new_name}", {},
    )
    return cast("OperationDict", _ok(result))


# ── Images ───────────────────────────────────────────────────────────


@_op(incus_write)
def create_image(
    source: Annotated[dict[str, Any], Field(description=_SOURCE_IMAGE_DESC)],
    public: Annotated[bool, Field(description="Make the image publicly readable.")] = False,
    auto_update: Annotated[
        bool, Field(description="Auto-refresh the image from its source periodically."),
    ] = False,
    properties: Annotated[dict[str, Any] | None,
        Field(description="Image metadata dict (arbitrary key/value)."),
    ] = _UNSET_DICT,
    project: _ProjectAnn = _UNSET_STR,
) -> OperationDict:
    """Create/import an image. Async. Register skipped: fingerprint unknown pre-wait."""
    body: dict[str, Any] = {
        "source": source,
        "public": public,
        "auto_update": auto_update,
    }
    if properties is not _UNSET:
        body["properties"] = properties
    result = _get_client().post("/1.0/images", json=body, params=_qp(project=project))
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_image(
    fingerprint: str,
    properties: Annotated[dict[str, Any] | None,
        Field(description="Image metadata dict (arbitrary key/value)."),
    ] = _UNSET_DICT,
    public: Annotated[
        bool | None, Field(description="Make the image publicly readable."),
    ] = _UNSET_BOOL,
    auto_update: Annotated[
        bool | None, Field(description="Auto-refresh the image from its source."),
    ] = _UNSET_BOOL,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update image properties (full replace)."""
    body: dict[str, Any] = {}
    if properties is not _UNSET:
        body["properties"] = properties
    if public is not _UNSET:
        body["public"] = public
    if auto_update is not _UNSET:
        body["auto_update"] = auto_update
    result = _get_client().put(
        f"/1.0/images/{fingerprint}", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def patch_image(
    fingerprint: str,
    properties: Annotated[dict[str, Any] | None,
        Field(description="Image metadata dict."),
    ] = _UNSET_DICT,
    public: Annotated[
        bool | None, Field(description="Make the image publicly readable."),
    ] = _UNSET_BOOL,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Partially update image properties."""
    body: dict[str, Any] = {}
    if properties is not _UNSET:
        body["properties"] = properties
    if public is not _UNSET:
        body["public"] = public
    result = _get_client().patch(
        f"/1.0/images/{fingerprint}", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def refresh_image(fingerprint: str) -> OperationDict:
    """Refresh an image from its source. Async. Register skipped: empty body."""
    return cast("OperationDict", _ok(_get_client().post(f"/1.0/images/{fingerprint}/refresh")))


@_op(incus_write)
def create_image_alias(
    name: str,
    target: Annotated[str, Field(description="Image fingerprint the alias points at.")],
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create an image alias."""
    body: dict[str, Any] = {"name": name, "target": target}
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/images/aliases", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_image_alias(
    name: str,
    target: Annotated[str, Field(description="Image fingerprint the alias points at.")],
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update an image alias target."""
    body: dict[str, Any] = {"target": target}
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/images/aliases/{name}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_image_alias(name: str, new_name: str) -> dict[str, Any]:
    """Rename an image alias."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(f"/1.0/images/aliases/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(
        result, body, f"/1.0/images/aliases/{new_name}", {},
    )
    return _ok(result)


# ── Networks ─────────────────────────────────────────────────────────


@_op(incus_write)
def create_network(
    name: str,
    type: Annotated[
        str,
        Field(description="Network type (bridge, ovn, physical, macvlan, sriov)."),
    ] = "bridge",
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a network. Async."""
    body: dict[str, Any] = {"name": name, "type": type}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    qp = _qp(project=project)
    result = _get_client().post("/1.0/networks", json=body, params=qp)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/networks/{name}", qp)
    return _ok(result)


@_op(incus_write)
def update_network(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update network configuration (full replace)."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/networks/{name}", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def patch_network(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Partially update network configuration."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().patch(
        f"/1.0/networks/{name}", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_network(name: str, new_name: str) -> dict[str, Any]:
    """Rename a network. Async."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(f"/1.0/networks/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/networks/{new_name}", {})
    return _ok(result)


@_op(incus_write)
def create_network_forward(
    network: str,
    listen_address: str,
    config: _ConfigAnn = _UNSET_DICT,
    ports: Annotated[
        list[dict[str, Any]] | None,
        Field(description="Forward port specs (list of {'protocol', 'listen_port', 'target_port', 'target_address'})."),
    ] = _UNSET_LIST_DICT,
) -> dict[str, Any]:
    """Create a network address forward."""
    body: dict[str, Any] = {"listen_address": listen_address}
    if config is not _UNSET:
        body["config"] = config
    if ports is not _UNSET:
        body["ports"] = ports
    result = _get_client().post(f"/1.0/networks/{network}/forwards", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_network_forward(
    network: str,
    listen_address: str,
    config: _ConfigAnn = _UNSET_DICT,
    ports: Annotated[
        list[dict[str, Any]] | None,
        Field(description="Forward port specs."),
    ] = _UNSET_LIST_DICT,
) -> dict[str, Any]:
    """Update a network address forward."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if ports is not _UNSET:
        body["ports"] = ports
    result = _get_client().put(
        f"/1.0/networks/{network}/forwards/{listen_address}", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def create_load_balancer(
    network: str,
    listen_address: str,
    config: _ConfigAnn = _UNSET_DICT,
    backends: Annotated[
        list[dict[str, Any]] | None,
        Field(description="Backend specs (list of {'name', 'target_address', 'target_port'})."),
    ] = _UNSET_LIST_DICT,
    ports: Annotated[
        list[dict[str, Any]] | None,
        Field(description="LB port specs."),
    ] = _UNSET_LIST_DICT,
) -> dict[str, Any]:
    """Create a network load balancer."""
    body: dict[str, Any] = {"listen_address": listen_address}
    if config is not _UNSET:
        body["config"] = config
    if backends is not _UNSET:
        body["backends"] = backends
    if ports is not _UNSET:
        body["ports"] = ports
    result = _get_client().post(
        f"/1.0/networks/{network}/load-balancers", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_load_balancer(
    network: str,
    listen_address: str,
    config: _ConfigAnn = _UNSET_DICT,
    backends: Annotated[
        list[dict[str, Any]] | None, Field(description="Backend specs."),
    ] = _UNSET_LIST_DICT,
    ports: Annotated[
        list[dict[str, Any]] | None, Field(description="LB port specs."),
    ] = _UNSET_LIST_DICT,
) -> dict[str, Any]:
    """Update a network load balancer."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if backends is not _UNSET:
        body["backends"] = backends
    if ports is not _UNSET:
        body["ports"] = ports
    result = _get_client().put(
        f"/1.0/networks/{network}/load-balancers/{listen_address}", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def create_network_peer(
    network: str,
    name: str,
    target_network: Annotated[
        str, Field(description="Peer network name in the target project."),
    ],
    target_project: Annotated[
        str | None,
        Field(description="Target project (defaults to caller's project)."),
    ] = _UNSET_STR,
    config: _ConfigAnn = _UNSET_DICT,
) -> OperationDict:
    """Create a network peer."""
    body: dict[str, Any] = {"name": name, "target_network": target_network}
    if target_project is not _UNSET:
        body["target_project"] = target_project
    if config is not _UNSET:
        body["config"] = config
    result = _get_client().post(f"/1.0/networks/{network}/peers", json=body)
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_network_peer(
    network: str,
    peer: str,
    config: _ConfigAnn = _UNSET_DICT,
) -> dict[str, Any]:
    """Update a network peer."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    result = _get_client().put(f"/1.0/networks/{network}/peers/{peer}", json=body)
    _verify_response(body, result)
    return _ok(result)


# ── Network ACLs ─────────────────────────────────────────────────────


@_op(incus_write)
def create_network_acl(
    name: str,
    egress: Annotated[
        list[dict[str, Any]] | None,
        Field(description="Egress rules (each rule: action/destination/protocol/...)."),
    ] = _UNSET_LIST_DICT,
    ingress: Annotated[
        list[dict[str, Any]] | None, Field(description="Ingress rules (same schema as egress)."),
    ] = _UNSET_LIST_DICT,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a network ACL."""
    body: dict[str, Any] = {"name": name}
    if egress is not _UNSET:
        body["egress"] = egress
    if ingress is not _UNSET:
        body["ingress"] = ingress
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/network-acls", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_network_acl(
    name: str,
    egress: Annotated[
        list[dict[str, Any]] | None, Field(description="Egress rules."),
    ] = _UNSET_LIST_DICT,
    ingress: Annotated[
        list[dict[str, Any]] | None, Field(description="Ingress rules."),
    ] = _UNSET_LIST_DICT,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a network ACL (full replace)."""
    body: dict[str, Any] = {}
    if egress is not _UNSET:
        body["egress"] = egress
    if ingress is not _UNSET:
        body["ingress"] = ingress
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/network-acls/{name}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_network_acl(name: str, new_name: str) -> dict[str, Any]:
    """Rename a network ACL."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(f"/1.0/network-acls/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/network-acls/{new_name}", {})
    return _ok(result)


# ── Network Address Sets ─────────────────────────────────────────────


@_op(incus_write)
def create_network_address_set(
    name: str,
    addresses: Annotated[
        list[str] | None,
        Field(description="IP addresses or CIDR ranges."),
    ] = _UNSET_LIST_STR,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a network address set."""
    body: dict[str, Any] = {"name": name}
    if addresses is not _UNSET:
        body["addresses"] = addresses
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/network-address-sets", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_network_address_set(
    name: str,
    addresses: Annotated[
        list[str] | None,
        Field(description="IP addresses or CIDR ranges."),
    ] = _UNSET_LIST_STR,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a network address set."""
    body: dict[str, Any] = {}
    if addresses is not _UNSET:
        body["addresses"] = addresses
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/network-address-sets/{name}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_network_address_set(name: str, new_name: str) -> dict[str, Any]:
    """Rename a network address set."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/network-address-sets/{name}", json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result, body, f"/1.0/network-address-sets/{new_name}", {},
    )
    return _ok(result)


# ── Network Integrations ─────────────────────────────────────────────


@_op(incus_write)
def create_network_integration(
    name: str,
    type: Annotated[str, Field(description="Integration type (e.g. 'ovn').")],
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a network integration."""
    body: dict[str, Any] = {"name": name, "type": type}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/network-integrations", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_network_integration(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a network integration."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/network-integrations/{name}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_network_integration(name: str, new_name: str) -> dict[str, Any]:
    """Rename a network integration."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/network-integrations/{name}", json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result, body, f"/1.0/network-integrations/{new_name}", {},
    )
    return _ok(result)


# ── Network Zones ────────────────────────────────────────────────────


@_op(incus_write)
def create_network_zone(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a network zone (DNS)."""
    body: dict[str, Any] = {"name": name}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/network-zones", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_network_zone(
    zone: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a network zone."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/network-zones/{zone}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def create_zone_record(
    zone: str,
    name: str,
    entries: Annotated[
        list[dict[str, Any]] | None,
        Field(description="DNS record entries (list of {'type': 'A', 'value': '10.0.0.1', ...})."),
    ] = _UNSET_LIST_DICT,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a DNS record in a network zone."""
    body: dict[str, Any] = {"name": name}
    if entries is not _UNSET:
        body["entries"] = entries
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post(
        f"/1.0/network-zones/{zone}/records", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_zone_record(
    zone: str,
    name: str,
    entries: Annotated[
        list[dict[str, Any]] | None, Field(description="DNS record entries."),
    ] = _UNSET_LIST_DICT,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a DNS record in a network zone."""
    body: dict[str, Any] = {}
    if entries is not _UNSET:
        body["entries"] = entries
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/network-zones/{zone}/records/{name}", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


# ── Storage Pools ────────────────────────────────────────────────────


@_op(incus_write)
def create_storage_pool(
    name: str,
    driver: Annotated[
        str, Field(description="Storage driver (zfs, btrfs, dir, lvm, ceph, cephfs, ...)."),
    ],
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a storage pool."""
    body: dict[str, Any] = {"name": name, "driver": driver}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/storage-pools", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_storage_pool(
    pool: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update storage pool configuration."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/storage-pools/{pool}", json=body)
    _verify_response(body, result)
    return _ok(result)


# ── Storage Volumes ──────────────────────────────────────────────────


@_op(incus_write)
def create_volume(
    pool: str,
    name: str,
    type: Annotated[
        str,
        Field(description="Volume type (custom, container, image, virtual-machine)."),
    ] = "custom",
    config: _ConfigAnn = _UNSET_DICT,
    content_type: Annotated[
        str | None,
        Field(description="Volume content type ('filesystem' or 'block')."),
    ] = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> OperationDict:
    """Create a storage volume. Async."""
    body: dict[str, Any] = {"name": name, "type": type}
    if config is not _UNSET:
        body["config"] = config
    if content_type is not _UNSET:
        body["content_type"] = content_type
    qp = _qp(project=project)
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/volumes", json=body, params=qp,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result, body, f"/1.0/storage-pools/{pool}/volumes/{type}/{name}", qp,
    )
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_volume(
    pool: str,
    type: str,
    volume: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update storage volume configuration."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}",
        json=body,
        params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_volume(pool: str, type: str, volume: str, new_name: str) -> OperationDict:
    """Rename/move a storage volume. Async."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}", json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result,
        body,
        f"/1.0/storage-pools/{pool}/volumes/{type}/{new_name}",
        {},
    )
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def create_volume_snapshot(
    pool: str,
    type: str,
    volume: str,
    snapshot_name: str,
) -> OperationDict:
    """Create a volume snapshot."""
    body: dict[str, Any] = {"name": snapshot_name}
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots",
        json=body,
    )
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_volume_snapshot(
    pool: str,
    type: str,
    volume: str,
    snapshot: str,
    expires_at: Annotated[
        str | None,
        Field(description="Expiration timestamp (RFC3339)."),
    ] = _UNSET_STR,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update volume snapshot properties."""
    body: dict[str, Any] = {}
    if expires_at is not _UNSET:
        body["expires_at"] = expires_at
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}",
        json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_volume_snapshot(
    pool: str,
    type: str,
    volume: str,
    snapshot: str,
    new_name: str,
) -> OperationDict:
    """Rename a volume snapshot."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{snapshot}",
        json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result,
        body,
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots/{new_name}",
        {},
    )
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def create_volume_backup(
    pool: str,
    type: str,
    volume: str,
    backup_name: Annotated[
        str | None,
        Field(description="Backup name (auto-generated when omitted)."),
    ] = _UNSET_STR,
    compression_algorithm: Annotated[
        str | None,
        Field(description="Compression algorithm (e.g. 'gzip')."),
    ] = _UNSET_STR,
    volume_only: Annotated[
        bool, Field(description="Exclude related volumes from the backup."),
    ] = False,
    optimized_storage: Annotated[
        bool,
        Field(description="Use storage-driver-specific format."),
    ] = False,
) -> OperationDict:
    """Create a volume backup. Async. Register skipped when backup_name auto-generated."""
    body: dict[str, Any] = {"volume_only": volume_only, "optimized_storage": optimized_storage}
    if backup_name is not _UNSET and backup_name:
        body["name"] = backup_name
    if compression_algorithm is not _UNSET and compression_algorithm:
        body["compression_algorithm"] = compression_algorithm
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups", json=body,
    )
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def rename_volume_backup(
    pool: str, type: str, volume: str, backup: str, new_name: str,
) -> OperationDict:
    """Rename a volume backup."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups/{backup}",
        json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result,
        body,
        f"/1.0/storage-pools/{pool}/volumes/{type}/{volume}/backups/{new_name}",
        {},
    )
    return cast("OperationDict", _ok(result))


# ── Storage Buckets ──────────────────────────────────────────────────


@_op(incus_write)
def create_bucket(
    pool: str,
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a storage bucket."""
    body: dict[str, Any] = {"name": name}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post(f"/1.0/storage-pools/{pool}/buckets", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_bucket(
    pool: str,
    bucket: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update storage bucket configuration."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/storage-pools/{pool}/buckets/{bucket}", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def create_bucket_key(
    pool: str,
    bucket: str,
    name: str,
    role: Annotated[
        str, Field(description="Access role ('read-only' or 'admin')."),
    ] = "read-only",
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a storage bucket access key."""
    body: dict[str, Any] = {"name": name, "role": role}
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_bucket_key(
    pool: str,
    bucket: str,
    key: str,
    role: Annotated[
        str | None, Field(description="Access role ('read-only' or 'admin')."),
    ] = _UNSET_STR,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a storage bucket access key."""
    body: dict[str, Any] = {}
    if role is not _UNSET:
        body["role"] = role
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/storage-pools/{pool}/buckets/{bucket}/keys/{key}", json=body,
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def create_bucket_backup(
    pool: str,
    bucket: str,
    backup_name: Annotated[
        str | None,
        Field(description="Backup name (auto-generated when omitted)."),
    ] = _UNSET_STR,
    compression_algorithm: Annotated[
        str | None, Field(description="Compression algorithm (e.g. 'gzip')."),
    ] = _UNSET_STR,
) -> OperationDict:
    """Create a storage bucket backup."""
    body: dict[str, Any] = {}
    if backup_name is not _UNSET and backup_name:
        body["name"] = backup_name
    if compression_algorithm is not _UNSET and compression_algorithm:
        body["compression_algorithm"] = compression_algorithm
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups", json=body,
    )
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def rename_bucket_backup(pool: str, bucket: str, backup: str, new_name: str) -> OperationDict:
    """Rename a storage bucket backup."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(
        f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups/{backup}",
        json=body,
    )
    _verify_response(body, result)
    _register_pending_verify(
        result,
        body,
        f"/1.0/storage-pools/{pool}/buckets/{bucket}/backups/{new_name}",
        {},
    )
    return cast("OperationDict", _ok(result))


# ── Profiles ─────────────────────────────────────────────────────────


@_op(incus_write)
def create_profile(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    devices: _DevicesAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a profile."""
    body: dict[str, Any] = {"name": name}
    if config is not _UNSET:
        body["config"] = config
    if devices is not _UNSET:
        body["devices"] = devices
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post(
        "/1.0/profiles", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_profile(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    devices: _DevicesAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    project: _ProjectAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a profile (full replace)."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if devices is not _UNSET:
        body["devices"] = devices
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(
        f"/1.0/profiles/{name}", json=body, params=_qp(project=project),
    )
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_profile(name: str, new_name: str) -> dict[str, Any]:
    """Rename a profile."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(f"/1.0/profiles/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/profiles/{new_name}", {})
    return _ok(result)


# ── Projects ─────────────────────────────────────────────────────────


@_op(incus_write)
def create_project(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a project."""
    body: dict[str, Any] = {"name": name}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/projects", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_project(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a project (full replace)."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/projects/{name}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_project(name: str, new_name: str) -> OperationDict:
    """Rename a project."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(f"/1.0/projects/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/projects/{new_name}", {})
    return cast("OperationDict", _ok(result))


# ── Cluster ──────────────────────────────────────────────────────────


@_op(incus_write)
def update_cluster(
    server_name: Annotated[
        str | None, Field(description="Cluster server name."),
    ] = _UNSET_STR,
    enabled: Annotated[
        bool | None, Field(description="Whether clustering is enabled."),
    ] = _UNSET_BOOL,
    cluster_address: Annotated[
        str | None, Field(description="Cluster network address (host:port)."),
    ] = _UNSET_STR,
) -> dict[str, Any]:
    """Update cluster configuration."""
    body: dict[str, Any] = {}
    if server_name is not _UNSET:
        body["server_name"] = server_name
    if enabled is not _UNSET:
        body["enabled"] = enabled
    if cluster_address is not _UNSET:
        body["cluster_address"] = cluster_address
    result = _get_client().put("/1.0/cluster", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_cluster_certificate(
    cluster_certificate: Annotated[
        str, Field(description="PEM-encoded cluster certificate."),
    ],
    cluster_certificate_key: Annotated[
        str,
        Field(description="PEM-encoded cluster private key (write-only; never echoed back)."),
    ],
) -> dict[str, Any]:
    """Update the cluster certificate. Verify skipped: private key isn't round-tripped."""
    body: dict[str, Any] = {
        "cluster_certificate": cluster_certificate,
        "cluster_certificate_key": cluster_certificate_key,
    }
    return _ok(_get_client().put("/1.0/cluster/certificate", json=body))


@_op(incus_write)
def request_join_token(name: str) -> OperationDict:
    """Request a cluster join token for a new member."""
    body: dict[str, Any] = {"server_name": name}
    result = _get_client().post("/1.0/cluster/members", json=body)
    _verify_response(body, result)
    return cast("OperationDict", _ok(result))


@_op(incus_write)
def update_cluster_member(
    name: str,
    config: _ConfigAnn = _UNSET_DICT,
    description: _DescriptionAnn = _UNSET_STR,
    groups: Annotated[
        list[str] | None,
        Field(description="Cluster group names this member belongs to."),
    ] = _UNSET_LIST_STR,
) -> dict[str, Any]:
    """Update cluster member configuration."""
    body: dict[str, Any] = {}
    if config is not _UNSET:
        body["config"] = config
    if description is not _UNSET:
        body["description"] = description
    if groups is not _UNSET:
        body["groups"] = groups
    result = _get_client().put(f"/1.0/cluster/members/{name}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_cluster_member(name: str, new_name: str) -> dict[str, Any]:
    """Rename a cluster member."""
    body: dict[str, Any] = {"server_name": new_name}
    result = _get_client().post(f"/1.0/cluster/members/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/cluster/members/{new_name}", {})
    return _ok(result)


@_op(incus_write)
def create_cluster_group(
    name: str,
    members: Annotated[
        list[str] | None,
        Field(description="Cluster member names to include in the group."),
    ] = _UNSET_LIST_STR,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Create a cluster group."""
    body: dict[str, Any] = {"name": name}
    if members is not _UNSET:
        body["members"] = members
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().post("/1.0/cluster/groups", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_cluster_group(
    name: str,
    members: Annotated[
        list[str] | None,
        Field(description="Cluster member names to include."),
    ] = _UNSET_LIST_STR,
    description: _DescriptionAnn = _UNSET_STR,
) -> dict[str, Any]:
    """Update a cluster group."""
    body: dict[str, Any] = {}
    if members is not _UNSET:
        body["members"] = members
    if description is not _UNSET:
        body["description"] = description
    result = _get_client().put(f"/1.0/cluster/groups/{name}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def rename_cluster_group(name: str, new_name: str) -> dict[str, Any]:
    """Rename a cluster group."""
    body: dict[str, Any] = {"name": new_name}
    result = _get_client().post(f"/1.0/cluster/groups/{name}", json=body)
    _verify_response(body, result)
    _register_pending_verify(result, body, f"/1.0/cluster/groups/{new_name}", {})
    return _ok(result)


# ── Certificates ─────────────────────────────────────────────────────


@_op(incus_write)
def add_certificate(
    certificate: Annotated[str, Field(description="PEM-encoded certificate.")],
    name: Annotated[
        str | None, Field(description="Human-readable name for the certificate."),
    ] = _UNSET_STR,
    type: Annotated[
        str, Field(description="Certificate type (usually 'client')."),
    ] = "client",
    restricted: Annotated[
        bool,
        Field(description="Restrict this cert to specific projects (see 'projects')."),
    ] = False,
    projects: Annotated[
        list[str] | None,
        Field(description="Project names this cert is restricted to."),
    ] = _UNSET_LIST_STR,
) -> dict[str, Any]:
    """Add a trusted certificate."""
    body: dict[str, Any] = {
        "certificate": certificate,
        "type": type,
        "restricted": restricted,
    }
    if name is not _UNSET and name:
        body["name"] = name
    if projects is not _UNSET:
        body["projects"] = projects
    result = _get_client().post("/1.0/certificates", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_write)
def update_certificate(
    fingerprint: str,
    certificate: Annotated[
        str | None, Field(description="PEM-encoded certificate."),
    ] = _UNSET_STR,
    name: Annotated[
        str | None, Field(description="Human-readable name."),
    ] = _UNSET_STR,
    restricted: Annotated[
        bool | None, Field(description="Restrict to specific projects."),
    ] = _UNSET_BOOL,
    projects: Annotated[
        list[str] | None,
        Field(description="Restricted project names."),
    ] = _UNSET_LIST_STR,
) -> dict[str, Any]:
    """Update a trusted certificate."""
    body: dict[str, Any] = {}
    if certificate is not _UNSET:
        body["certificate"] = certificate
    if name is not _UNSET:
        body["name"] = name
    if restricted is not _UNSET:
        body["restricted"] = restricted
    if projects is not _UNSET:
        body["projects"] = projects
    result = _get_client().put(f"/1.0/certificates/{fingerprint}", json=body)
    _verify_response(body, result)
    return _ok(result)
