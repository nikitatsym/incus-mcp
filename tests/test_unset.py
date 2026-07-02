"""Contract tests for the `_UNSET` sentinel.

Pin the identity/truthiness/repr semantics before later steps start
consuming `_UNSET` in tool signatures and body-builders.
"""

from __future__ import annotations

from incus_mcp.registry import _UNSET, _Unset


def test_singleton_identity():
    assert _Unset() is _UNSET
    assert _Unset() is _Unset()


def test_falsy():
    assert bool(_UNSET) is False


def test_repr():
    assert repr(_UNSET) == "_UNSET"


def test_distinct_from_none():
    assert _UNSET is not None
    assert _UNSET != None  # noqa: E711 - identity vs equality is the point
