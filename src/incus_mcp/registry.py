from __future__ import annotations

from typing import Any, Callable, TypeVar


class Group:
    __slots__ = ("name", "doc")

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

    _instance: "_Unset | None" = None

    def __new__(cls) -> "_Unset":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "_UNSET"

    def __bool__(self) -> bool:
        return False


# `Any` by design: tool signatures declare their public type (e.g. `str |
# None`) and use `_UNSET` as the default. If `_UNSET` were typed as
# `_Unset`, every `x is _UNSET` gate would trip `comparison-overlap`.
_UNSET: Any = _Unset()


F = TypeVar("F", bound=Callable[..., Any])


def _op(group: Group) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        if not fn.__doc__:
            raise RuntimeError(f"Tool function {fn.__name__!r} has no docstring")
        setattr(fn, "_mcp_group", group)
        return fn
    return decorator
