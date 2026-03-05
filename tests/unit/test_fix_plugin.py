"""
Unit tests for src/responseiq/plugins/fix.py

Coverage matrix:
  - no --target arg              → error state
  - non-existent target          → error state
  - target with empty content    → no_incidents state
  - only LOW/MEDIUM incidents    → no_actionable_incidents state (triage filter)
  - HIGH severity incident       → success state, RemediationService called
  - CRITICAL severity incident   → success state, sorted first
  - top-3 cap                    → at most 3 RemediationService calls even with > 3 HIGH incidents
  - _collect_messages directory  → aggregates *.log / *.txt / *.json across sub-dirs
  - _read_file unreadable path   → logs warning, returns empty list
  - asyncio gather concurrency   → analyze_log_async called once per message
"""

from unittest.mock import AsyncMock, MagicMock, patch

from responseiq.plugins.fix import FixPlugin
from responseiq.schemas.incident import IncidentOut


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_incident_out(
    title: str = "Test Incident",
    severity: str = "high",
    source: str = "test_source",
) -> IncidentOut:
    return IncidentOut(title=title, severity=severity, source=source, description="desc")


def _make_recommendation(title: str = "Fix It", allowed: bool = True) -> MagicMock:
    rec = MagicMock()
    rec.to_dict.return_value = {
        "incident_id": "abc-123",
        "title": title,
        "severity": "high",
        "confidence": 0.9,
        "impact_score": 80.0,
        "blast_radius": "service-local",
        "rationale": "root cause identified",
        "remediation_plan": "patch line 42",
        "allowed": allowed,
        "execution_mode": "suggest_only",
        "rollback_plan": "git revert HEAD",
        "test_plan": "pytest tests/",
        "checks_passed": ["policy_ok", "safety_ok"],
        "checks_failed": [],
        "next_steps": ["Open PR", "Review"],
        "proof_bundle": None,
        "proof_integrity": None,
        "correlation": None,
        "causal_graph": None,
        "llm_model_used": "llama3.2",
    }
    return rec


def _build_state(target: str | None = None) -> dict:
    return {"context": {"args": {"target": target}}}


# ---------------------------------------------------------------------------
# 1. Argument / path validation
# ---------------------------------------------------------------------------


class TestFixPluginValidation:
    def test_no_target_returns_error(self):
        plugin = FixPlugin()
        state = plugin.run({"context": {"args": {}}})
        assert state["fix_result"] == "error"
        assert "No --target" in state["fix_error"]

    def test_missing_target_key_returns_error(self):
        plugin = FixPlugin()
        state = plugin.run({})
        assert state["fix_result"] == "error"

    def test_nonexistent_target_returns_error(self, tmp_path):
        plugin = FixPlugin()
        state = plugin.run(_build_state(str(tmp_path / "does_not_exist.log")))
        assert state["fix_result"] == "error"
        assert "not found" in state["fix_error"].lower()

    def test_empty_file_returns_no_incidents(self, tmp_path):
        log = tmp_path / "empty.log"
        log.write_text("")
        plugin = FixPlugin()
        state = plugin.run(_build_state(str(log)))
        assert state["fix_result"] == "no_incidents"
        assert state["fixes"] == []


# ---------------------------------------------------------------------------
# 2. Triage filter — only HIGH and CRITICAL pass through
# ---------------------------------------------------------------------------


class TestTriageFilter:
    def _run_with_incidents(self, tmp_path, incident_outs: list) -> dict:
        log = tmp_path / "test.log"
        log.write_text("\n".join(f"msg {i}" for i in range(len(incident_outs))))
        plugin = FixPlugin()

        async def _fake_analyze(msg):
            idx = int(msg.split()[-1])
            return incident_outs[idx] if idx < len(incident_outs) else None

        with patch("responseiq.services.analyzer.analyze_log_async", side_effect=_fake_analyze):
            state = plugin.run(_build_state(str(log)))
        return state

    def test_only_low_incidents_produces_no_actionable(self, tmp_path):
        incidents = [_make_incident_out(severity="low"), _make_incident_out(severity="medium")]
        state = self._run_with_incidents(tmp_path, incidents)
        assert state["fix_result"] == "no_actionable_incidents"
        assert state["fixes"] == []

    def test_medium_incidents_are_excluded(self, tmp_path):
        incidents = [_make_incident_out(severity="medium")] * 3
        state = self._run_with_incidents(tmp_path, incidents)
        assert state["fix_result"] == "no_actionable_incidents"

    def test_none_result_from_analyzer_skipped(self, tmp_path):
        # If LLM returns None for all messages, no incidents to fix
        log = tmp_path / "test.log"
        log.write_text("something bad happened")
        plugin = FixPlugin()
        with patch("responseiq.services.analyzer.analyze_log_async", new_callable=AsyncMock, return_value=None):
            state = plugin.run(_build_state(str(log)))
        assert state["fix_result"] == "no_actionable_incidents"


# ---------------------------------------------------------------------------
# 3. Successful remediation path
# ---------------------------------------------------------------------------


class TestSuccessfulRemediation:
    def _patched_run(self, tmp_path, incidents: list, recommendations: list) -> dict:
        log = tmp_path / "app.log"
        log.write_text("\n".join(f"incident line {i}" for i in range(len(incidents))))
        plugin = FixPlugin()

        rec_iter = iter(recommendations)

        async def _fake_analyze(msg):
            idx = int(msg.split()[-1])
            return incidents[idx] if idx < len(incidents) else None

        async def _fake_remediate(inc, context_path=None):
            return next(rec_iter)

        with (
            patch("responseiq.services.analyzer.analyze_log_async", side_effect=_fake_analyze),
            patch(
                "responseiq.services.remediation_service.RemediationService.remediate_incident",
                side_effect=_fake_remediate,
            ),
        ):
            return plugin.run(_build_state(str(log)))

    def test_single_high_incident_success(self, tmp_path):
        incidents = [_make_incident_out(severity="high")]
        recs = [_make_recommendation()]
        state = self._patched_run(tmp_path, incidents, recs)
        assert state["fix_result"] == "success"
        assert len(state["fixes"]) == 1
        assert state["fixes"][0]["title"] == "Fix It"

    def test_critical_incident_remediated(self, tmp_path):
        incidents = [_make_incident_out(severity="critical", title="OOM Killer")]
        recs = [_make_recommendation(title="Increase heap")]
        state = self._patched_run(tmp_path, incidents, recs)
        assert state["fix_result"] == "success"
        assert state["total_fixed"] == 1

    def test_total_scanned_reflects_input_lines(self, tmp_path):
        incidents = [_make_incident_out(severity="high")] * 4
        recs = [_make_recommendation()] * 3  # top 3 cap
        state = self._patched_run(tmp_path, incidents, recs)
        assert state["total_scanned"] == 4

    def test_top_3_cap_limits_remediation_calls(self, tmp_path):
        """4 HIGH incidents → only 3 RemediationService calls."""
        incidents = [_make_incident_out(severity="high", title=f"Inc {i}") for i in range(4)]
        recs = [_make_recommendation(title=f"Fix {i}") for i in range(3)]
        state = self._patched_run(tmp_path, incidents, recs)
        assert len(state["fixes"]) == 3
        assert state["total_fixed"] == 3

    def test_critical_sorted_before_high(self, tmp_path):
        """CRITICAL incident should appear first in fixes list."""
        incidents = [
            _make_incident_out(severity="high", title="High Inc"),
            _make_incident_out(severity="critical", title="Critical Inc"),
        ]
        # recs ordered as they'll be requested after severity sort
        recs = [_make_recommendation(title="Critical Fix"), _make_recommendation(title="High Fix")]
        state = self._patched_run(tmp_path, incidents, recs)
        assert state["fixes"][0]["title"] == "Critical Fix"

    def test_recommendation_fields_preserved(self, tmp_path):
        incidents = [_make_incident_out(severity="high")]
        rec = _make_recommendation(allowed=False)
        state = self._patched_run(tmp_path, incidents, [rec])
        fix = state["fixes"][0]
        assert fix["allowed"] is False
        assert fix["rollback_plan"] == "git revert HEAD"
        assert fix["test_plan"] == "pytest tests/"
        assert fix["checks_passed"] == ["policy_ok", "safety_ok"]


# ---------------------------------------------------------------------------
# 4. File collection helpers
# ---------------------------------------------------------------------------


class TestCollectMessages:
    def test_single_txt_file(self, tmp_path):
        f = tmp_path / "app.txt"
        f.write_text("line one\nline two\n\nline three")
        plugin = FixPlugin()
        msgs = plugin._collect_messages(f)
        assert msgs == ["line one", "line two", "line three"]

    def test_directory_collects_log_and_txt(self, tmp_path):
        (tmp_path / "a.log").write_text("log line")
        (tmp_path / "b.txt").write_text("txt line")
        plugin = FixPlugin()
        msgs = plugin._collect_messages(tmp_path)
        assert "log line" in msgs
        assert "txt line" in msgs

    def test_directory_collects_nested(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.log").write_text("nested msg")
        plugin = FixPlugin()
        msgs = plugin._collect_messages(tmp_path)
        assert "nested msg" in msgs

    def test_blank_lines_excluded(self, tmp_path):
        f = tmp_path / "app.log"
        f.write_text("\n\n  \nreal line\n\n")
        plugin = FixPlugin()
        msgs = plugin._collect_messages(f)
        assert msgs == ["real line"]

    def test_unreadable_file_returns_empty(self, tmp_path):
        plugin = FixPlugin()
        result = plugin._read_file(tmp_path / "ghost.log")
        assert result == []


# ---------------------------------------------------------------------------
# 5. analyze_log_async called once per message (concurrency guard)
# ---------------------------------------------------------------------------


class TestConcurrency:
    def test_gather_calls_analyzer_for_each_message(self, tmp_path):
        """analyze_log_async must be called exactly once per non-blank line."""
        log = tmp_path / "multi.log"
        log.write_text("msg A\nmsg B\nmsg C")
        plugin = FixPlugin()

        call_args: list[str] = []

        async def _tracking_analyze(msg):
            call_args.append(msg)
            return _make_incident_out(severity="low")  # below triage threshold

        with patch("responseiq.services.analyzer.analyze_log_async", side_effect=_tracking_analyze):
            plugin.run(_build_state(str(log)))

        assert call_args == ["msg A", "msg B", "msg C"]
