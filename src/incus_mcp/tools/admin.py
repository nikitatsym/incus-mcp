from __future__ import annotations

from typing import Annotated, Any, Literal, cast

from pydantic import Field

from ..registry import _UNSET, _op
from .groups import incus_admin
from .helpers import _get_client, _ok, _verify_response

_WARNING_STATUS_DESC = "Warning lifecycle status."
_UNSET_STATUS = cast("Literal['new', 'acknowledged'] | None", _UNSET)


@_op(incus_admin)
def update_server_config(
    config: Annotated[dict[str, Any],
        Field(
            description=(
                "Server-wide config map (e.g. {'core.https_address': ':8443'})."
            ),
        ),
    ],
) -> dict[str, Any]:
    """Update server configuration (full replace)."""
    body: dict[str, Any] = {"config": config}
    result = _get_client().put("/1.0", json=body)
    _verify_response(body, result)
    return _ok(result)


@_op(incus_admin)
def patch_server_config(
    config: Annotated[dict[str, Any],
        Field(description="Server-wide config keys to merge into existing config."),
    ],
) -> dict[str, Any]:
    """Partially update server configuration (merge)."""
    body: dict[str, Any] = {"config": config}
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
) -> dict[str, Any]:
    """Acknowledge or reset a warning (full replace)."""
    body: dict[str, Any] = {"status": status}
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
) -> dict[str, Any]:
    """Partially update a warning."""
    body: dict[str, Any] = {}
    if status is not _UNSET:
        body["status"] = status
    result = _get_client().patch(f"/1.0/warnings/{uuid}", json=body)
    _verify_response(body, result)
    return _ok(result)
