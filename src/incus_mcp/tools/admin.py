from __future__ import annotations

from ..registry import _op
from .groups import incus_admin
from .helpers import _get_client, _ok


@_op(incus_admin)
def update_server_config(config: dict):
    """Update server configuration (full replace)."""
    return _ok(_get_client().put("/1.0", json={"config": config}))


@_op(incus_admin)
def patch_server_config(config: dict):
    """Partially update server configuration."""
    return _ok(_get_client().patch("/1.0", json={"config": config}))


@_op(incus_admin)
def update_warning(uuid: str, status: str):
    """Acknowledge/dismiss a warning. status: new, acknowledged."""
    return _ok(_get_client().put(f"/1.0/warnings/{uuid}", json={"status": status}))


@_op(incus_admin)
def patch_warning(uuid: str, status: str | None = None):
    """Partially update a warning."""
    body: dict = {}
    if status is not None:
        body["status"] = status
    return _ok(_get_client().patch(f"/1.0/warnings/{uuid}", json=body))
