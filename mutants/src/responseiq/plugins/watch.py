# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Watch plugin — continuous log tail / event subscription daemon.

Tails a log file (or reads from stdin / a named pipe) indefinitely and
triggers the full Detect → Context → Reason pipeline automatically
for every new error line. This is the daemon mode:

    responseiq --mode watch --target ./logs/app.log
    docker logs -f <container> | responseiq --mode watch --target -
    kubectl logs -f <pod>      | responseiq --mode watch --target -

The watcher debounces bursts: when more than ``BURST_LIMIT`` error lines
arrive within ``BURST_WINDOW_SECS``, they are batched into a single
analysis call to avoid hammering the LLM during an alert storm.
"""

from __future__ import annotations

import asyncio
import signal
import sys
import time
from pathlib import Path
from typing import List

from loguru import logger

from .base import BasePlugin

BURST_LIMIT = 5
BURST_WINDOW_SECS = 3.0
_ERROR_KEYWORDS = ("error", "exception", "traceback", "fatal", "critical", "panic", "oom")


def _is_error_line(line: str) -> bool:
    lower = line.lower()
    return any(kw in lower for kw in _ERROR_KEYWORDS)


class WatchPlugin(BasePlugin):
    """Daemon plugin: tail a log source and auto-trigger analysis on errors."""

    def run(self, agent_state: dict) -> dict:
        agent_state = agent_state.copy()
        target = agent_state.get("context", {}).get("args", {}).get("target")
        if not target:
            agent_state["watch_result"] = "error"
            agent_state["watch_error"] = "No --target specified. Use --target <log_file> or --target - for stdin."
            return agent_state

        print("\033[1;36m  ResponseIQ Watch Mode — tailing log source. Press Ctrl+C to stop.\033[0m")
        if target == "-":
            print("\033[2m  Reading from stdin — pipe your log stream in.\033[0m\n")
        else:
            print(f"\033[2m  Watching: {target}\033[0m\n")

        try:
            asyncio.run(self._watch_loop(target))
        except KeyboardInterrupt:
            print("\n\033[2m  Watch mode stopped.\033[0m")

        agent_state["watch_result"] = "stopped"
        return agent_state

    # ------------------------------------------------------------------
    async def _watch_loop(self, target: str) -> None:
        """Main tail loop — yields batches to the analysis handler."""
        loop = asyncio.get_running_loop()

        # Handle SIGTERM gracefully
        stop_event = asyncio.Event()
        if sys.platform != "win32":
            loop.add_signal_handler(signal.SIGTERM, stop_event.set)

        pending: List[str] = []
        burst_start: float = 0.0

        async for line in self._line_source(target, stop_event):
            if not _is_error_line(line):
                continue

            now = time.monotonic()
            if not pending:
                burst_start = now

            pending.append(line.strip())

            # Flush burst window when full or time expired
            if len(pending) >= BURST_LIMIT or (now - burst_start) >= BURST_WINDOW_SECS:
                await self._handle_burst(pending)
                pending.clear()

        # Flush any remaining lines on clean exit
        if pending:
            await self._handle_burst(pending)

    async def _line_source(self, target: str, stop_event: asyncio.Event):
        """Async generator that yields new log lines as they arrive."""
        if target == "-":
            # stdin mode — read until EOF
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
            while not stop_event.is_set():
                try:
                    raw = await asyncio.wait_for(reader.readline(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                if not raw:
                    break
                yield raw.decode(errors="replace")
        else:
            path = Path(target)
            if not path.exists():
                logger.error(f"Watch target not found: {target}")
                return

            # Seek to end of existing content (tail -f behaviour)
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(0, 2)  # seek to EOF
                while not stop_event.is_set():
                    line = fh.readline()
                    if line:
                        yield line
                    else:
                        await asyncio.sleep(0.1)

    async def _handle_burst(self, lines: List[str]) -> None:
        """Analyse a batch of error lines and print the summary."""
        from responseiq.services.analyzer import analyze_log_async

        combined = "\n".join(lines)
        print(f"\033[33m  [{time.strftime('%H:%M:%S')}] Detected {len(lines)} error line(s) — analysing...\033[0m")

        try:
            result = await analyze_log_async(combined)
            if result:
                sev = (result.severity or "?").upper() if hasattr(result, "severity") else "?"
                title = result.title if hasattr(result, "title") else str(result)
                colour = "\033[31m" if sev in ("HIGH", "CRITICAL") else "\033[33m"
                print(f"{colour}  [{sev}] {title}\033[0m")
                if hasattr(result, "description") and result.description:
                    desc = str(result.description)[:200]
                    print(f"\033[2m  {desc}\033[0m")
            else:
                print("\033[2m  No actionable incident detected.\033[0m")
        except Exception as exc:
            logger.warning(f"Watch analysis error: {exc}")

        print()
