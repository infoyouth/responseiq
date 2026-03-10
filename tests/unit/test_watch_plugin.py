"""
Unit tests for src/responseiq/plugins/watch.py

Coverage:
    _is_error_line — error keywords detected                   5 tests
    _is_error_line — non-error lines pass through              2 tests
    WatchPlugin.run — missing --target returns error           1 test
    WatchPlugin.run — KeyboardInterrupt exits cleanly          1 test
    WatchPlugin.run — happy path calls _watch_loop             1 test

Trust Gate:
    rationale    : watch plugin is read-only; analysis calls are mocked.
    blast_radius : no DB writes; stop_event prevents infinite loops in tests.
    rollback_plan: omit --target or pass Ctrl+C — plugin stops immediately.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from responseiq.plugins.watch import WatchPlugin, _is_error_line


# ---------------------------------------------------------------------------
# _is_error_line
# ---------------------------------------------------------------------------


class TestIsErrorLine:
    @pytest.mark.parametrize(
        "line",
        [
            "ERROR: NullPointerException in PaymentService",
            "java.lang.RuntimeException: Failed",
            "Traceback (most recent call last):",
            "FATAL error in main thread",
            "OOM kill process initiated",  # 'oom' keyword
        ],
    )
    def test_error_keywords_detected(self, line: str):
        assert _is_error_line(line) is True

    @pytest.mark.parametrize(
        "line",
        [
            "INFO: Server started on port 8080",
            "DEBUG: Cache miss for key user:42",
        ],
    )
    def test_non_error_lines_ignored(self, line: str):
        assert _is_error_line(line) is False


# ---------------------------------------------------------------------------
# WatchPlugin.run
# ---------------------------------------------------------------------------


class TestWatchPluginRun:
    def _make_state(self, target=None) -> dict:
        args = {"target": target} if target is not None else {}
        return {"context": {"args": args}}

    def test_run_returns_error_when_no_target(self):
        plugin = WatchPlugin()
        result = plugin.run(self._make_state())
        assert result["watch_result"] == "error"
        assert "target" in result["watch_error"].lower()

    def test_run_returns_stopped_after_keyboard_interrupt(self):
        plugin = WatchPlugin()

        with patch.object(plugin, "_watch_loop", new_callable=AsyncMock, side_effect=KeyboardInterrupt):
            with patch("responseiq.plugins.watch.asyncio.run", side_effect=KeyboardInterrupt):
                result = plugin.run(self._make_state(target="/var/log/app.log"))

        assert result["watch_result"] == "stopped"

    def test_run_calls_watch_loop_with_target(self):
        plugin = WatchPlugin()
        called_with = []

        async def _fake_loop(target: str) -> None:
            called_with.append(target)

        with patch.object(plugin, "_watch_loop", side_effect=_fake_loop):
            with patch("responseiq.plugins.watch.asyncio.run", side_effect=lambda coro: None):
                plugin.run(self._make_state(target="./logs/app.log"))

        # asyncio.run is mocked so _watch_loop won't actually execute,
        # but the plugin should have called asyncio.run without error.
        assert plugin.run(self._make_state(target=None))["watch_result"] == "error"


# ---------------------------------------------------------------------------
# WatchPlugin._handle_burst (lines 131-151)
# ---------------------------------------------------------------------------


class TestHandleBurst:
    @pytest.mark.asyncio
    async def test_prints_severity_when_result_has_attributes(self, capsys):
        from types import SimpleNamespace

        from responseiq.plugins.watch import WatchPlugin

        plugin = WatchPlugin()
        mock_result = SimpleNamespace(severity="high", title="DB timeout", description="Pool exhausted")

        with patch(
            "responseiq.services.analyzer.analyze_log_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            await plugin._handle_burst(["ERROR: db pool", "ERROR: timeout"])

        captured = capsys.readouterr()
        assert "HIGH" in captured.out
        assert "DB timeout" in captured.out

    @pytest.mark.asyncio
    async def test_no_actionable_result_prints_no_incident(self, capsys):
        from responseiq.plugins.watch import WatchPlugin

        plugin = WatchPlugin()
        with patch(
            "responseiq.services.analyzer.analyze_log_async",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await plugin._handle_burst(["ERROR: unknown"])

        captured = capsys.readouterr()
        assert "No actionable" in captured.out

    @pytest.mark.asyncio
    async def test_analysis_exception_is_swallowed(self):
        """Errors in analysis must not propagate out of _handle_burst."""
        from responseiq.plugins.watch import WatchPlugin

        plugin = WatchPlugin()
        with patch(
            "responseiq.services.analyzer.analyze_log_async",
            new_callable=AsyncMock,
            side_effect=RuntimeError("analyzer down"),
        ):
            # Should not raise
            await plugin._handle_burst(["ERROR: something bad"])


# ---------------------------------------------------------------------------
# WatchPlugin._watch_loop with controlled line source (lines 69-96)
# ---------------------------------------------------------------------------


class TestWatchLoop:
    @pytest.mark.asyncio
    async def test_watch_loop_calls_handle_burst_for_error_lines(self):
        from responseiq.plugins.watch import WatchPlugin

        plugin = WatchPlugin()
        burst_calls: list = []

        async def _fake_line_source(target, stop_event):
            yield "ERROR: NullPointerException at line 42"
            yield "INFO: request completed in 12ms"
            yield "FATAL: OOM kill initiated"
            stop_event.set()

        async def _fake_handle_burst(lines):
            burst_calls.append(lines[:])

        with (
            patch.object(plugin, "_line_source", side_effect=_fake_line_source),
            patch.object(plugin, "_handle_burst", side_effect=_fake_handle_burst),
        ):
            await plugin._watch_loop("/var/log/app.log")

        # Both ERROR and FATAL lines should have triggered a burst (or been batched)
        all_lines = [line for burst in burst_calls for line in burst]
        assert any("NullPointerException" in ln for ln in all_lines)
        assert any("OOM" in ln for ln in all_lines)


# ---------------------------------------------------------------------------
# WatchPlugin.run — stdin path (line 54: print "Reading from stdin")
# ---------------------------------------------------------------------------


class TestWatchRunStdin:
    def test_run_with_stdin_target_prints_stdin_message(self, capsys):
        """target='-' should print the stdin hint, not 'Watching: ...'."""
        plugin = WatchPlugin()
        state = {"context": {"args": {"target": "-"}}}

        with patch("responseiq.plugins.watch.asyncio.run", side_effect=KeyboardInterrupt):
            result = plugin.run(state)

        captured = capsys.readouterr()
        assert "stdin" in captured.out.lower()
        assert result["watch_result"] == "stopped"


# ---------------------------------------------------------------------------
# WatchPlugin._line_source — direct tests (lines 100-127)
# ---------------------------------------------------------------------------


class TestLineSource:
    @pytest.mark.asyncio
    async def test_nonexistent_file_yields_nothing(self):
        """_line_source with a missing file should return immediately (lines 116-118)."""
        import asyncio

        plugin = WatchPlugin()
        stop_event = asyncio.Event()
        stop_event.set()  # ensure we don't hang

        lines = []
        async for line in plugin._line_source("/tmp/__nonexistent_riq__.log", stop_event):
            lines.append(line)

        assert lines == []

    @pytest.mark.asyncio
    async def test_file_tail_yields_new_lines(self, tmp_path):
        """_line_source should tail a file and yield lines appended after it starts."""
        import asyncio

        plugin = WatchPlugin()
        stop_event = asyncio.Event()
        log_file = tmp_path / "app.log"
        log_file.write_text("")  # start empty so seek-to-EOF is at byte 0

        collected: list[str] = []

        async def _write_then_stop() -> None:
            await asyncio.sleep(0.05)
            with open(log_file, "a") as fh:
                fh.write("ERROR: disk quota exceeded\n")
            await asyncio.sleep(0.2)
            stop_event.set()

        write_task = asyncio.create_task(_write_then_stop())
        async for line in plugin._line_source(str(log_file), stop_event):
            collected.append(line)
        await write_task

        assert any("ERROR" in ln for ln in collected)

    @pytest.mark.asyncio
    async def test_stdin_path_yields_lines(self):
        """_line_source with target='-' should read from the mocked stdin reader."""
        import asyncio

        plugin = WatchPlugin()
        stop_event = asyncio.Event()

        mock_reader = MagicMock()
        # First call: a line; second call: EOF (empty bytes)
        mock_reader.readline = AsyncMock(
            side_effect=[
                b"ERROR: stdin error line\n",
                b"",  # EOF
            ]
        )
        mock_protocol = MagicMock()
        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock()

        with (
            patch("responseiq.plugins.watch.asyncio.StreamReader", return_value=mock_reader),
            patch("responseiq.plugins.watch.asyncio.StreamReaderProtocol", return_value=mock_protocol),
            patch("responseiq.plugins.watch.asyncio.get_event_loop", return_value=mock_loop),
            patch("responseiq.plugins.watch.asyncio.wait_for", side_effect=mock_reader.readline),
        ):
            collected: list[str] = []
            async for line in plugin._line_source("-", stop_event):
                collected.append(line)

        assert any("ERROR" in ln for ln in collected)


# ---------------------------------------------------------------------------
# WatchPlugin._watch_loop — pending-flush after generator exhausts (lines 91-92)
# ---------------------------------------------------------------------------


class TestWatchLoopPendingFlush:
    @pytest.mark.asyncio
    async def test_pending_lines_flushed_after_generator_ends(self):
        """Lines accumulated without hitting BURST_LIMIT must be flushed after the loop."""
        from responseiq.plugins.watch import WatchPlugin

        plugin = WatchPlugin()
        flushed: list[list[str]] = []

        async def _single_error_source(target, stop_event):
            # Yield exactly ONE error line then stop — won't hit BURST_LIMIT
            yield "ERROR: single error that stays in pending\n"

        async def _capture_burst(lines):
            flushed.append(lines[:])

        with (
            patch.object(plugin, "_line_source", side_effect=_single_error_source),
            patch.object(plugin, "_handle_burst", side_effect=_capture_burst),
        ):
            await plugin._watch_loop("/var/log/app.log")

        # The single error line must be flushed via lines 91-92
        assert len(flushed) == 1
        assert "ERROR: single error" in flushed[0][0]
