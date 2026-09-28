# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""ResponseIQ MCP Server.

Exposes ResponseIQ's core capabilities as **Model Context Protocol** tools,
allowing Claude Desktop, VS Code Copilot, Cursor, and other MCP-aware agents
to trigger incident analysis, remediation generation, trust-gate validation,
and GitHub PR creation directly from chat.

Tools:
    - ``analyze_incident``     Classify severity + generate summary
    - ``get_remediation``      Generate a full remediation plan
    - ``run_trust_gate``       Validate a proposed fix against 7-rule trust gate
    - ``open_pr``              Open a GitHub PR for an approved remediation

Activation:
    pip install 'responseiq[mcp]'
    responseiq-mcp   # runs the server on stdio

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
        "mcpServers": {
            "responseiq": {
                "command": "responseiq-mcp"
            }
        }
    }
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from responseiq.utils.logger import logger

# Fail fast with a clear message when the optional dep is missing.
try:
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.server.stdio import stdio_server  # type: ignore[import-untyped]
    from mcp import types as mcp_types  # type: ignore[import-untyped]
except ImportError as _exc:  # pragma: no cover
    raise SystemExit(
        "ResponseIQ MCP server requires 'mcp>=1.0.0'.\nInstall it with:  pip install 'responseiq[mcp]'"
    ) from _exc

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

server: Server = Server("responseiq")

# ---------------------------------------------------------------------------
# Tool: analyze_incident
# ---------------------------------------------------------------------------


@server.list_tools()  # type: ignore[misc]
async def _list_tools() -> list[mcp_types.Tool]:
    return [
        mcp_types.Tool(
            name="analyze_incident",
            description=(
                "Analyse a raw log snippet or stack trace. Returns a severity "
                "classification (critical/high/medium/low), a one-line title, "
                "key contributing factors, and a brief summary."
            ),
            inputSchema={
                "type": "object",
                "required": ["log_text"],
                "properties": {
                    "log_text": {
                        "type": "string",
                        "description": "Raw log content or stack trace to analyse",
                    },
                    "code_context": {
                        "type": "string",
                        "description": "Optional source code snippets referenced in the trace",
                        "default": "",
                    },
                },
            },
        ),
        mcp_types.Tool(
            name="get_remediation",
            description=(
                "Generate a surgical remediation plan for an incident. Returns a "
                "structured plan including root-cause, code patch, rollback plan, "
                "blast radius, and rationale."
            ),
            inputSchema={
                "type": "object",
                "required": ["log_text"],
                "properties": {
                    "log_text": {
                        "type": "string",
                        "description": "Raw log content or stack trace describing the incident",
                    },
                    "code_context": {
                        "type": "string",
                        "description": "Source code context extracted from relevant files",
                        "default": "",
                    },
                },
            },
        ),
        mcp_types.Tool(
            name="run_trust_gate",
            description=(
                "Validate a proposed fix against ResponseIQ's 7-rule Trust Gate. "
                "Returns pass/fail per rule plus an overall APPROVED or REJECTED verdict."
            ),
            inputSchema={
                "type": "object",
                "required": ["fix_code"],
                "properties": {
                    "fix_code": {
                        "type": "string",
                        "description": "The proposed code patch or remediation to validate",
                    },
                    "fix_rationale": {
                        "type": "string",
                        "description": "Explanation of why the fix is safe",
                        "default": "",
                    },
                },
            },
        ),
        mcp_types.Tool(
            name="open_pr",
            description=(
                "Open a GitHub Pull Request with the provided patch. Requires "
                "RESPONSEIQ_GITHUB_TOKEN and RESPONSEIQ_GITHUB_REPO to be configured. "
                "In dry-run mode (no token) this returns the PR payload without creating it."
            ),
            inputSchema={
                "type": "object",
                "required": ["remediation_plan"],
                "properties": {
                    "remediation_plan": {
                        "type": "object",
                        "description": "Full remediation plan object as returned by get_remediation",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, return the PR payload without actually creating it",
                        "default": False,
                    },
                },
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------


@server.call_tool()  # type: ignore[misc]
async def _call_tool(name: str, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
    except Exception as exc:
        logger.exception("MCP tool %s failed: %s", name, exc)
        result = {"error": str(exc), "tool": name}

    return [mcp_types.TextContent(type="text", text=json.dumps(result, default=str, indent=2))]


async def _dispatch(name: str, args: dict[str, Any]) -> Any:  # noqa: PLR0912
    if name == "analyze_incident":
        return await _tool_analyze_incident(
            log_text=args["log_text"],
            code_context=args.get("code_context", ""),
        )
    if name == "get_remediation":
        return await _tool_get_remediation(
            log_text=args["log_text"],
            code_context=args.get("code_context", ""),
        )
    if name == "run_trust_gate":
        return await _tool_run_trust_gate(
            fix_code=args["fix_code"],
            fix_rationale=args.get("fix_rationale", ""),
        )
    if name == "open_pr":
        return await _tool_open_pr(
            remediation_plan=args["remediation_plan"],
            dry_run=args.get("dry_run", False),
        )
    return {"error": f"Unknown tool: {name!r}"}


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def _tool_analyze_incident(log_text: str, code_context: str = "") -> dict[str, Any]:
    from responseiq.services.analysis_service import analyze_log_async  # type: ignore[import]

    result = await analyze_log_async(log_text)
    return {
        "severity": result.get("severity", "unknown"),
        "title": result.get("title", ""),
        "summary": result.get("summary", ""),
        "contributing_factors": result.get("contributing_factors", []),
        "code_context_provided": bool(code_context),
    }


async def _tool_get_remediation(log_text: str, code_context: str = "") -> dict[str, Any]:
    from responseiq.services.remediation_service import RemediationService

    svc = RemediationService()
    incident: dict[str, Any] = {"log_content": log_text, "code_context": code_context}
    recommendation = await svc.remediate_incident(incident=incident)
    return recommendation.model_dump() if hasattr(recommendation, "model_dump") else recommendation.__dict__


async def _tool_run_trust_gate(fix_code: str, fix_rationale: str = "") -> dict[str, Any]:
    import uuid

    from responseiq.services.trust_gate import RemediationRequest, TrustGateValidator

    validator = TrustGateValidator()
    req = RemediationRequest(
        incident_id=str(uuid.uuid4()),
        severity="medium",
        confidence=0.8,
        impact_score=0.5,
        blast_radius="unknown",
        affected_files=[],
        proposed_changes=[{"patch": fix_code}],
        rationale=fix_rationale,
    )
    verdict = await validator.validate_remediation(req)
    return verdict.model_dump() if hasattr(verdict, "model_dump") else verdict.__dict__


async def _tool_open_pr(remediation_plan: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    from responseiq.config.settings import settings

    # PR creation is handled inside remediate_incident; this tool surfaces the plan payload.
    if dry_run or not settings.github_token:
        return {
            "dry_run": True,
            "pr_payload": remediation_plan,
            "message": (
                "Dry-run mode — PR not created. Set RESPONSEIQ_GITHUB_TOKEN to enable. "
                "Use the full remediate_incident flow to trigger auto-PR creation."
            ),
        }

    pr_url = remediation_plan.get("pr_url") or remediation_plan.get("github_pr_url")
    return {
        "dry_run": False,
        "pr_url": pr_url,
        "message": (
            "PR URL extracted from remediation plan. "
            "Trigger a full remediate_incident call with your incident data to auto-create the PR."
        ),
        "plan_summary": {k: remediation_plan[k] for k in list(remediation_plan)[:8]},
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:  # pragma: no cover
    """Run the ResponseIQ MCP server on stdio."""
    logger.info("ResponseIQ MCP server starting on stdio…")
    asyncio.run(_run())


async def _run() -> None:  # pragma: no cover
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":  # pragma: no cover
    main()
