"""
samples/buggy_service.py — Intentionally broken service.

This module ships with ResponseIQ so you can run a real scan in under 60 seconds
without setting up your own logs or LLM key.

Bugs deliberately embedded:
  1. Unbounded list growth  → memory leak on repeated calls
  2. Missing None-guard     → AttributeError when user has no 'email' field
  3. Integer division       → ZeroDivisionError when request_count hits 0 after reset
"""

from __future__ import annotations

import time
from typing import Any

# ── Simulated in-memory "database" ───────────────────────────────────────────
_request_log: list[dict[str, Any]] = []    # BUG 1: never pruned → grows forever
_request_count: int = 0


def process_user_request(user: dict[str, Any], payload: str) -> dict[str, Any]:
    """
    Handle an incoming user request.

    Expected ``user`` shape::

        {
            "id": "u-123",
            "name": "Alice",
            "email": "alice@example.com"   # may be absent for OAuth users
        }
    """
    global _request_count

    # BUG 2: user["email"] raises KeyError / AttributeError if field is absent
    recipient = user["email"].lower()

    _request_count += 1

    # append every call — never evicted
    _request_log.append(
        {
            "ts": time.time(),
            "user": user.get("id", "unknown"),
            "payload_len": len(payload),
        }
    )

    # BUG 3: if _request_count is reset externally to 0 between the increment
    #         and this line, ZeroDivisionError occurs (race condition in tests)
    avg_payload = sum(r["payload_len"] for r in _request_log) / _request_count

    return {
        "status": "ok",
        "recipient": recipient,
        "request_number": _request_count,
        "avg_payload_bytes": avg_payload,
    }


def reset_counters() -> None:
    """Reset request counters — intentionally races with process_user_request."""
    global _request_count
    _request_log.clear()
    _request_count = 0          # sets to 0 AFTER log is cleared → ZeroDivisionError window


if __name__ == "__main__":
    # Simulate a short burst of requests to trigger the bugs
    users = [
        {"id": "u-001", "name": "Alice", "email": "alice@example.com"},
        {"id": "u-002", "name": "Bob"},          # missing email  → BUG 2
        {"id": "u-003", "name": "Carol", "email": "carol@example.com"},
    ]

    for u in users:
        try:
            result = process_user_request(u, payload="hello world")
            print(f"[OK]    {u['name']}: {result}")
        except Exception as exc:
            # This stack trace is what crash.log captures
            import traceback
            print(f"[ERROR] {u['name']}: {exc}")
            traceback.print_exc()
