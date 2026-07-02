"""Contract tests for `_verify_response`."""

from __future__ import annotations

import pytest

from incus_mcp.tools.helpers import _verify_response


def test_empty_sent_is_noop():
    _verify_response({}, {"anything": 1})
    _verify_response({}, {})


@pytest.mark.parametrize("received", [None, "text", ["list"], 42])
def test_non_dict_received_is_noop(received):
    _verify_response({"name": "x"}, received)


def test_flat_pass():
    _verify_response(
        {"name": "x"},
        {"name": "x", "type": "container"},
    )


def test_flat_drop():
    with pytest.raises(ValueError, match=r"'description'"):
        _verify_response(
            {"name": "x", "description": "d"},
            {"name": "x"},
        )


def test_recursive_pass():
    _verify_response(
        {"config": {"limits.cpu": "2"}},
        {"config": {"limits.cpu": "2", "volatile.uuid": "abcd"}},
    )


def test_recursive_drop():
    with pytest.raises(ValueError, match=r"'config\.limits\.cpu'"):
        _verify_response(
            {"config": {"limits.cpu": "2"}},
            {"config": {}},
        )


def test_deeply_nested_drop():
    with pytest.raises(ValueError, match=r"'devices\.eth0\.nictype'"):
        _verify_response(
            {"devices": {"eth0": {"nictype": "bridged"}}},
            {"devices": {"eth0": {}}},
        )


def test_empty_sent_dict_accepts_anything():
    _verify_response({"config": {}}, {"config": {}})
    _verify_response({"config": {}}, {"config": {"volatile.uuid": "x"}})


def test_value_normalisation_tolerated():
    # Presence-only check; wire may coerce "2" -> 2.
    _verify_response(
        {"config": {"limits.cpu": "2"}},
        {"config": {"limits.cpu": 2}},
    )


def test_root_skip_applies_at_root():
    _verify_response(
        {"source": {"type": "image", "alias": "ubuntu/24.04"}, "name": "x"},
        {"name": "x"},
    )


def test_root_skip_does_not_apply_nested_source():
    with pytest.raises(ValueError, match=r"'devices\.root\.source'"):
        _verify_response(
            {"devices": {"root": {"source": "/dev/xvda"}}},
            {"devices": {"root": {}}},
        )


def test_root_skip_does_not_apply_nested_mode():
    with pytest.raises(ValueError, match=r"'devices\.disk\.mode'"):
        _verify_response(
            {"devices": {"disk": {"mode": "0755"}}},
            {"devices": {"disk": {}}},
        )


def test_async_task_response_short_circuits():
    _verify_response(
        {"name": "x", "config": {"limits.cpu": "2"}},
        {
            "class": "task",
            "id": "op-uuid",
            "status": "Running",
            "status_code": 103,
            "metadata": {"class": "task", "resources": {"instances": ["/1.0/instances/x"]}},
        },
    )
