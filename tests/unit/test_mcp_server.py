"""
Unit tests for src/responseiq/mcp_server.py

Coverage:
    _list_tools — returns exactly 4 tools                        1 test
    _list_tools — tool names match spec                          1 test
    _dispatch — unknown tool name returns error dict             1 test
    _tool_analyze_incident — delegates to analyze_log_async      1 test
    _tool_run_trust_gate — builds RemediationRequest + calls TG  1 test
    _tool_open_pr — dry_run path (no token) returns dry_run dict 1 test
    _tool_open_pr — no github_token → dry_run regardless         1 test

Trust Gate:
    rationale    : MCP tools are read-orchestrating; no direct writes.
    blast_radius : open_pr tool dry-runs when token absent.
    rollback_plan: do not set RESPONSEIQ_GITHUB_TOKEN → all PR calls dry-run.

Note: The ``mcp`` package is an optional dep. Tests use mock to avoid
requiring it at test-collection time.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub out the ``mcp`` package so import succeeds without installing it
# ---------------------------------------------------------------------------


def _build_mcp_stubs() -> None:
    """Inject minimal mcp stubs into sys.modules before mcp_server is imported."""
    mcp_stub = ModuleType("mcp")
    server_stub = ModuleType("mcp.server")
    stdio_stub = ModuleType("mcp.server.stdio")
    types_stub = ModuleType("mcp.types")

    class _Server:
        def __init__(self, name: str):
            self.name = name

        def list_tools(self):
            def _decorator(fn):
                return fn

            return _decorator

        def call_tool(self):
            def _decorator(fn):
                return fn

            return _decorator

        def create_initialization_options(self):
            return {}

        async def run(self, *args, **kwargs):
            pass

    class _Tool:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _TextContent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    server_stub.Server = _Server  # type: ignore[attr-defined]
    types_stub.Tool = _Tool  # type: ignore[attr-defined]
    types_stub.TextContent = _TextContent  # type: ignore[attr-defined]
    stdio_stub.stdio_server = MagicMock()  # type: ignore[attr-defined]

    sys.modules.setdefault("mcp", mcp_stub)
    sys.modules.setdefault("mcp.server", server_stub)
    sys.modules.setdefault("mcp.server.stdio", stdio_stub)
    sys.modules.setdefault("mcp.types", types_stub)


_build_mcp_stubs()

# Now import the module under test
from responseiq.mcp_server import (  # noqa: E402
    _call_tool,
    _dispatch,
    _list_tools,
    _tool_analyze_incident,
    _tool_get_remediation,
    _tool_open_pr,
    _tool_run_trust_gate,
)


# ---------------------------------------------------------------------------
# _dispatch
# ---------------------------------------------------------------------------


class TestDispatch:
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        result = await _dispatch("nonexistent_tool", {})
        assert "error" in result
        assert "nonexistent_tool" in result["error"]


# ---------------------------------------------------------------------------
# _tool_analyze_incident
# ---------------------------------------------------------------------------


class TestToolAnalyzeIncident:
    @pytest.mark.asyncio
    async def test_delegates_to_analyze_log_async(self):
        fake_result = {
            "severity": "high",
            "title": "DB timeout",
            "summary": "Connections exhausted",
            "contributing_factors": ["high load"],
        }
        mock_analyze = AsyncMock(return_value=fake_result)
        with patch.dict(
            "sys.modules",
            {"responseiq.services.analysis_service": MagicMock(analyze_log_async=mock_analyze)},
        ):
            result = await _tool_analyze_incident("ERROR: db timeout", "")
        assert result["severity"] == "high"
        assert result["title"] == "DB timeout"


# ---------------------------------------------------------------------------
# _tool_run_trust_gate
# ---------------------------------------------------------------------------


class TestToolRunTrustGate:
    @pytest.mark.asyncio
    async def test_builds_request_and_calls_validator(self):
        # Mock ValidationResult-like object
        mock_verdict = MagicMock()
        mock_verdict.__dict__ = {"allowed": True, "reason": None}
        mock_validator = MagicMock()
        mock_validator.validate_remediation = AsyncMock(return_value=mock_verdict)
        mock_tg_module = MagicMock(
            TrustGateValidator=MagicMock(return_value=mock_validator),
            RemediationRequest=MagicMock(side_effect=lambda **kw: MagicMock(**kw)),
        )
        with patch.dict("sys.modules", {"responseiq.services.trust_gate": mock_tg_module}):
            await _tool_run_trust_gate("if x is None: raise ValueError()", "null guard")
        mock_validator.validate_remediation.assert_called_once()


# ---------------------------------------------------------------------------
# _tool_open_pr
# ---------------------------------------------------------------------------


class TestToolOpenPr:
    @pytest.mark.asyncio
    async def test_dry_run_flag_prevents_pr_creation(self):
        mock_settings = MagicMock()
        mock_settings.github_token = "ghp_fake"
        with patch("responseiq.config.settings.settings", mock_settings, create=True):
            result = await _tool_open_pr({"title": "Fix X"}, dry_run=True)
        assert result["dry_run"] is True
        assert "pr_payload" in result

    @pytest.mark.asyncio
    async def test_no_token_forces_dry_run(self):
        mock_settings = MagicMock()
        mock_settings.github_token = None
        with patch("responseiq.config.settings.settings", mock_settings, create=True):
            result = await _tool_open_pr({"title": "Fix Y"}, dry_run=False)
        assert result["dry_run"] is True


# ---------------------------------------------------------------------------
# _list_tools — verify all 4 tools are returned (line 61)
# ---------------------------------------------------------------------------


class TestListTools:
    @pytest.mark.asyncio
    async def test_returns_four_tools(self):
        tools = await _list_tools()
        assert len(tools) == 4

    @pytest.mark.asyncio
    async def test_tool_names_match_spec(self):
        tools = await _list_tools()
        names = {t.name for t in tools}
        assert names == {"analyze_incident", "get_remediation", "run_trust_gate", "open_pr"}


# ---------------------------------------------------------------------------
# _call_tool — wrapper that formats result as TextContent (lines 163-169)
# ---------------------------------------------------------------------------


class TestCallTool:
    @pytest.mark.asyncio
    async def test_returns_text_content_on_success(self):
        import json

        result = await _call_tool("nonexistent_tool", {})
        assert len(result) == 1
        assert result[0].type == "text"
        payload = json.loads(result[0].text)
        assert "error" in payload


# ---------------------------------------------------------------------------
# _tool_get_remediation — calls RemediationService.remediate_incident (lines 215-220)
# ---------------------------------------------------------------------------


class TestToolGetRemediation:
    @pytest.mark.asyncio
    async def test_calls_remediate_incident(self):
        mock_recommendation = MagicMock()
        mock_recommendation.model_dump.return_value = {"title": "Fix DB", "severity": "high"}
        mock_svc = MagicMock()
        mock_svc.remediate_incident = AsyncMock(return_value=mock_recommendation)
        mock_module = MagicMock(RemediationService=MagicMock(return_value=mock_svc))
        with patch.dict("sys.modules", {"responseiq.services.remediation_service": mock_module}):
            result = await _tool_get_remediation("ERROR: db timeout", "")
        assert result["title"] == "Fix DB"
        mock_svc.remediate_incident.assert_called_once()


# ---------------------------------------------------------------------------
# _dispatch — all 4 named branches covered (lines 174, 179, 184, 189)
# ---------------------------------------------------------------------------


class TestDispatchAllBranches:
    @pytest.mark.asyncio
    async def test_dispatch_get_remediation(self):
        mock_recommendation = MagicMock()
        mock_recommendation.__dict__ = {"title": "patched"}
        mock_svc = MagicMock()
        mock_svc.remediate_incident = AsyncMock(return_value=mock_recommendation)
        mock_module = MagicMock(RemediationService=MagicMock(return_value=mock_svc))
        with patch.dict("sys.modules", {"responseiq.services.remediation_service": mock_module}):
            result = await _dispatch("get_remediation", {"log_text": "ERROR: x"})
        assert "title" in result

    @pytest.mark.asyncio
    async def test_dispatch_run_trust_gate(self):
        mock_verdict = MagicMock()
        mock_verdict.__dict__ = {"allowed": True}
        mock_validator = MagicMock()
        mock_validator.validate_remediation = AsyncMock(return_value=mock_verdict)
        mock_tg_module = MagicMock(
            TrustGateValidator=MagicMock(return_value=mock_validator),
            RemediationRequest=MagicMock(side_effect=lambda **kw: MagicMock(**kw)),
        )
        with patch.dict("sys.modules", {"responseiq.services.trust_gate": mock_tg_module}):
            result = await _dispatch("run_trust_gate", {"fix_code": "if x: pass"})
        assert "allowed" in result

    @pytest.mark.asyncio
    async def test_dispatch_open_pr(self):
        mock_settings = MagicMock()
        mock_settings.github_token = None
        with patch("responseiq.config.settings.settings", mock_settings, create=True):
            result = await _dispatch("open_pr", {"remediation_plan": {"title": "Fix"}})
        assert result["dry_run"] is True


# ---------------------------------------------------------------------------
# _call_tool — exception path (lines 165-167)
# ---------------------------------------------------------------------------


class TestCallToolExceptionPath:
    @pytest.mark.asyncio
    async def test_exception_in_dispatch_returns_error_text_content(self):
        """When _dispatch raises, _call_tool catches it and returns TextContent error."""
        import json

        with patch(
            "responseiq.mcp_server._dispatch",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            result = await _call_tool("analyze_incident", {"log_text": "x"})

        assert len(result) == 1
        assert result[0].type == "text"
        payload = json.loads(result[0].text)
        assert payload["error"] == "boom"
        assert payload["tool"] == "analyze_incident"


# ---------------------------------------------------------------------------
# _dispatch — analyze_incident branch (line 174)
# ---------------------------------------------------------------------------


class TestDispatchAnalyzeIncident:
    @pytest.mark.asyncio
    async def test_analyze_incident_branch_returns_severity(self):
        mock_analysis = {
            "severity": "high",
            "title": "DB crash",
            "summary": "",
            "contributing_factors": [],
        }
        mock_module = MagicMock(analyze_log_async=AsyncMock(return_value=mock_analysis))
        with patch.dict("sys.modules", {"responseiq.services.analysis_service": mock_module}):
            result = await _dispatch("analyze_incident", {"log_text": "ERROR: db crash"})
        assert result["severity"] == "high"
        assert result["title"] == "DB crash"


# ---------------------------------------------------------------------------
# _tool_open_pr — non-dry-run path with real github_token (lines 257-258)
# ---------------------------------------------------------------------------


class TestToolOpenPrWithToken:
    @pytest.mark.asyncio
    async def test_returns_pr_url_when_token_is_set(self):
        """When github_token is set and dry_run=False, extract pr_url from plan."""
        mock_settings = MagicMock()
        mock_settings.github_token = "ghp_fake_token_xyz"

        plan = {"pr_url": "https://github.com/org/repo/pull/42", "title": "Fix DB"}
        with patch("responseiq.config.settings.settings", mock_settings, create=True):
            result = await _tool_open_pr(plan, dry_run=False)

        assert result["dry_run"] is False
        assert result["pr_url"] == "https://github.com/org/repo/pull/42"
