from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar, cast

from typing_extensions import Self


class Group:
    __slots__ = ("doc", "name")

    def __init__(self, name: str, doc: str) -> None:
        self.name = name
        self.doc = doc


ROOT = Group("root", "")


class _Unset:
    """Sentinel singleton: caller did not pass this field.

    Distinct from None. None means "caller explicitly passed null" -
    Incus PUT/PATCH endpoints accept null on some nullable body fields
    (description, config, devices, profiles) as a clearing operation.
    Optional body params declared with default _UNSET carry the
    omitted-vs-cleared distinction through Pydantic validation
    (exclude_unset=True) and on to the wire.
    """

    _instance: _Unset | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        # _instance is typed _Unset (the base, non-generic slot) - Self here
        # is always exactly _Unset since nothing subclasses this sentinel.
        return cast(Self, cls._instance)

    def __repr__(self) -> str:
        return "_UNSET"

    def __bool__(self) -> bool:
        return False


# `Any` by design: tool signatures declare their public type (e.g. `str |
# None`) and use `_UNSET` as the default. If `_UNSET` were typed as
# `_Unset`, every `x is _UNSET` gate would trip `comparison-overlap`.
_UNSET: Any = _Unset()


# Dispatch metadata used to be read/written with literal getattr/setattr,
# which ruff 0.16 bans (B009/B010); plain attribute access needs a static
# shape instead. It is split in two because ROOT ops are registered straight
# with mcp.tool() and never pass through server._prepare_op, so they only
# ever carry the group tag. The single widening cast lives in _prepare_op,
# which is what makes the fuller shape true.
class TaggedFn(Protocol):
    """Tool function after `_op`: carries only the group tag."""

    __name__: str
    _mcp_group: Group

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class OpFn(TaggedFn, Protocol):
    """Grouped tool function after `server._prepare_op`: full dispatch metadata."""

    _mcp_params_model: type[Any]
    _mcp_doc_head: str
    _mcp_doc_body: str


F = TypeVar("F", bound=Callable[..., Any])


def _op(group: Group) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        if not fn.__doc__:
            raise RuntimeError(f"Tool function {fn.__name__!r} has no docstring")
        cast(TaggedFn, fn)._mcp_group = group
        return fn
    return decorator
