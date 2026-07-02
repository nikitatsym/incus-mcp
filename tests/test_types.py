"""Step 9 adversarial checks: mypy-strict deliverable invariants.

The signatures of the non-blocking waiter ops are the only user-visible
contract this step changed (amended §8d: int -> float on second-durations).
These tests attack that guarantee by pinning the JSON Schema output of the
wait ops, so a future revert of the float retype (or any other regression
in the params-model plumbing) fails loudly instead of silently narrowing
the accepted domain.
"""

from __future__ import annotations

import incus_mcp.server as server


def test_operation_wait_start_second_durations_are_number():
    schema = server._build_schema("incus_read", "OperationWaitStart")
    props = schema["properties"]
    # timeout / interval / max_lifetime are durations; publish as number so
    # fractional-second polls are accepted. See amended §8d in the plan.
    assert props["timeout"]["type"] == "number"
    assert props["interval"]["type"] == "number"
    assert props["max_lifetime"]["type"] == "number"
    # max_poll_failures stays a count.
    assert props["max_poll_failures"]["type"] == "integer"


def test_operation_wait_poll_max_block_is_number():
    schema = server._build_schema("incus_read", "OperationWaitPoll")
    assert schema["properties"]["max_block"]["type"] == "number"


def test_wait_snapshot_shape_matches_typed_dict():
    """`WaitHandle.snapshot()` must satisfy WaitSnapshotDict's required keys.

    Adversarial against §9f: if a future edit drops a required key from the
    snapshot dict (e.g. removes `verify_error`), the TypedDict layer would
    only complain under mypy - here we sample it at runtime too.
    """
    from incus_mcp import wait_registry as wr

    handle = wr.create_handle("op-uuid-x", {"timeout": 1.0, "interval": 1.0})
    try:
        snap = handle.snapshot()
        required = {
            "wait_id", "operation_id", "status", "status_code", "terminated",
            "timed_out", "polls", "elapsed_seconds", "started_at", "ended_at",
            "transitions", "verify_error", "enrichment_error",
        }
        missing = required - set(snap.keys())
        assert not missing, f"WaitSnapshotDict required keys missing: {missing}"
    finally:
        wr.clear()


def test_dict_str_any_renders_as_bare_dict_in_help():
    """`dict[str, Any]` is the opaque-JSON annotation; help must render `dict`.

    Adversarial: if the special-case in _type_to_str is dropped, help text
    would leak the strict-typing detail (`dict[str, any] | None`) that
    callers do not need.
    """
    help_text = server._build_help("incus_write", search="create_instance")
    assert "dict[str, any]" not in help_text
    # Positive: the current rendered form.
    assert "config?: dict | None" in help_text
