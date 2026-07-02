from __future__ import annotations

from typing import Annotated, Literal, cast

from pydantic import Field

from ..registry import _UNSET, _op
from .groups import incus_admin
from .helpers import _get_client, _ok, _verify_response

_WARNING_STATUS_DESC = "Warning lifecycle status."
_UNSET_STATUS = cast("Literal['new', 'acknowledged'] | None", _UNSET)


@_op(incus_admin)
def update_server_config(
    config: Annotated[
        dict,
        Field(
            description=(
                "Server-wide config map (e.g. {'core.https_address': ':8443'})."
            ),
        ),
    ],
):
    """Update server configuration (full replace)."""
    body: dict = {"config": config}
    result = _get_client().put("/1.0", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_admin)
def patch_server_config(
    config: Annotated[
        dict,
        Field(description="Server-wide config keys to merge into existing config."),
    ],
):
    """Partially update server configuration (merge)."""
    body: dict = {"config": config}
    result = _get_client().patch("/1.0", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_admin)
def update_warning(
    uuid: str,
    status: Annotated[
        Literal["new", "acknowledged"],
        Field(description=_WARNING_STATUS_DESC),
    ],
):
    """Acknowledge or reset a warning (full replace)."""
    body: dict = {"status": status}
    result = _get_client().put(f"/1.0/warnings/{uuid}", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_admin)
def patch_warning(
    uuid: str,
    status: Annotated[
        Literal["new", "acknowledged"] | None,
        Field(description=_WARNING_STATUS_DESC),
    ] = _UNSET_STATUS,
):
    """Partially update a warning."""
    body: dict = {}
    if status is not _UNSET:
        body["status"] = status
    result = _get_client().patch(f"/1.0/warnings/{uuid}", json=body)
    _verify_response(body, result)
    return _ok(result)
