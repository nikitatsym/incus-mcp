"""In-process registry of Incus async-operation wait handles.

Terminal handles reap after TTL. One polling task per handle owns writes;
readers grab a snapshot. Pattern: mcp-server-v2 spec, "Long-running waiters".
"""

from __future__ import annotations

import asyncio
import secrets
import time
from typing import Any

from .types import WaitSnapshotDict, WaitTransitionDict

# Incus terminal set: 200 = success, 400 = failure, 401 = cancelled.
TERMINAL_STATUS_CODES: frozenset[int] = frozenset({200, 400, 401})

_DEFAULT_TTL_SECONDS = 3600


class WaitHandle:
    """One long-running wait bound to an Incus operation."""

    __slots__ = (
        "wait_id",
        "operation_id",
        "options",
        "status",
        "status_code",
        "terminated",
        "timed_out",
        "polls",
        "poll_failures",
        "last_poll_error",
        "started_at",
        "ended_at",
        "last_payload",
        "transitions",
        "err",
        "verify_error",
        "enrichment_error",
        "task",
        "done_event",
    )

    wait_id: str
    operation_id: str
    options: dict[str, float]
    status: str | None
    status_code: int | None
    terminated: bool
    timed_out: bool
    polls: int
    poll_failures: int
    last_poll_error: str | None
    started_at: float
    ended_at: float | None
    last_payload: Any
    transitions: list[WaitTransitionDict]
    err: str | None
    verify_error: str | None
    enrichment_error: str | None
    task: asyncio.Task[None] | None
    done_event: asyncio.Event

    def __init__(
        self,
        wait_id: str,
        operation_id: str,
        options: dict[str, float],
    ) -> None:
        self.wait_id = wait_id
        self.operation_id = operation_id
        self.options = options

        self.status = None
        self.status_code = None
        self.terminated = False
        self.timed_out = False
        self.polls = 0
        self.poll_failures = 0
        self.last_poll_error = None
        self.started_at = time.time()
        self.ended_at = None
        self.last_payload = None
        self.transitions = []
        self.err = None
        self.verify_error = None
        self.enrichment_error = None

        self.task = None
        self.done_event = asyncio.Event()

    @property
    def elapsed_seconds(self) -> float:
        end = self.ended_at if self.ended_at is not None else time.time()
        return round(end - self.started_at, 2)

    def record_transition(
        self, new_status: str | None, new_status_code: int | None
    ) -> bool:
        if new_status == self.status and new_status_code == self.status_code:
            return False
        transition: WaitTransitionDict = {
            "from": self.status,
            "to": new_status,
            "status_code": new_status_code,
            "elapsed_seconds": round(time.time() - self.started_at, 2),
        }
        self.transitions.append(transition)
        self.status = new_status
        self.status_code = new_status_code
        return True

    def record_poll_failure(self, message: str) -> None:
        self.polls += 1
        self.poll_failures += 1
        self.last_poll_error = message

    def mark_terminated(self, *, err: str | None = None) -> None:
        self.terminated = err is None
        self.err = err
        self.ended_at = time.time()
        self.done_event.set()

    def mark_timed_out(self, message: str) -> None:
        self.timed_out = True
        self.err = message
        self.ended_at = time.time()
        self.done_event.set()

    def snapshot(self) -> WaitSnapshotDict:
        snap: WaitSnapshotDict = {
            "wait_id": self.wait_id,
            "operation_id": self.operation_id,
            "status": self.status,
            "status_code": self.status_code,
            "terminated": self.terminated,
            "timed_out": self.timed_out,
            "polls": self.polls,
            "elapsed_seconds": self.elapsed_seconds,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "transitions": list(self.transitions),
            "verify_error": self.verify_error,
            "enrichment_error": self.enrichment_error,
        }
        if self.poll_failures:
            snap["poll_failures"] = self.poll_failures
            snap["last_poll_error"] = self.last_poll_error
        if self.last_payload is not None:
            snap["operation"] = self.last_payload
        if self.err is not None:
            snap["error"] = self.err
        return snap


_registry: dict[str, WaitHandle] = {}


def create_handle(operation_id: str, options: dict[str, float]) -> WaitHandle:
    wait_id = f"w-{secrets.token_hex(4)}"
    handle = WaitHandle(wait_id, operation_id, options)
    _registry[wait_id] = handle
    return handle


def get_handle(wait_id: str) -> WaitHandle | None:
    return _registry.get(wait_id)


def list_handles() -> list[WaitHandle]:
    return list(_registry.values())


def reap_expired(now: float | None = None) -> int:
    now = now if now is not None else time.time()
    stale = [
        wid for wid, h in _registry.items()
        if h.ended_at is not None and (now - h.ended_at) > _DEFAULT_TTL_SECONDS
    ]
    for wid in stale:
        del _registry[wid]
    return len(stale)


def clear() -> None:
    """Cancel any running tasks and drop all handles. Test-only."""
    for h in _registry.values():
        if h.task is not None and not h.task.done():
            h.task.cancel()
    _registry.clear()
