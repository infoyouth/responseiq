"""
fix.py — ResponseIQ Fix Plugin

Runs the full remediation pipeline (scan → triage → Trust Gate → patch synthesis)
on a target log file or directory. Operates in suggest_only mode by default;
no code is written without an explicit policy upgrade.

Usage:
    responseiq --mode fix --target <file_or_dir>
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import List

from .base import BasePlugin

logger = logging.getLogger(__name__)


class FixPlugin(BasePlugin):
    def run(self, agent_state: dict) -> dict:
        agent_state = agent_state.copy()
        target = agent_state.get("context", {}).get("args", {}).get("target")

        if not target:
            agent_state["fix_result"] = "error"
            agent_state["fix_error"] = "No --target specified."
            return agent_state

        target_path = Path(target)
        if not target_path.exists():
            agent_state["fix_result"] = "error"
            agent_state["fix_error"] = f"Target not found: {target}"
            return agent_state

        messages = self._collect_messages(target_path)
        if not messages:
            agent_state["fix_result"] = "no_incidents"
            agent_state["fixes"] = []
            return agent_state

        async def _run_all(msgs: List[str]) -> list:
            from responseiq.services.analyzer import analyze_log_async
            from responseiq.services.remediation_service import RemediationService

            svc = RemediationService(environment="development")

            # Step 1: scan all messages concurrently
            scan_results = await asyncio.gather(*[analyze_log_async(m) for m in msgs])

            # Step 2: triage — pick incidents with severity >= high
            severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            incidents_to_fix = []
            for msg, result in zip(msgs, scan_results):
                if result is None:
                    continue
                sev = (result.severity or "low").lower()
                if severity_rank.get(sev, 0) >= 3:  # high and above only
                    incidents_to_fix.append(
                        {
                            "id": str(uuid.uuid4()),
                            "title": result.title,
                            "severity": sev,
                            "log_content": msg,
                            "source": result.source,
                        }
                    )

            if not incidents_to_fix:
                return []

            # Step 3: remediate top 3 (avoid hammering Ollama with all 11)
            top = sorted(
                incidents_to_fix,
                key=lambda x: severity_rank.get(x.get("severity") or "low", 0),
                reverse=True,
            )[:3]
            fixes = []
            for inc in top:
                sev_label = str(inc.get("severity") or "low").upper()
                logger.info(f"Remediating [{sev_label}] {inc['title']}")
                rec = await svc.remediate_incident(inc, context_path=target_path)
                fixes.append(rec.to_dict())

            return fixes

        fixes = asyncio.run(_run_all(messages))
        agent_state["fix_result"] = "success" if fixes else "no_actionable_incidents"
        agent_state["fixes"] = fixes
        agent_state["total_scanned"] = len(messages)
        agent_state["total_fixed"] = len(fixes)
        return agent_state

    def _collect_messages(self, path: Path) -> List[str]:
        if path.is_file():
            return self._read_file(path)
        messages: List[str] = []
        for pattern in ("*.json", "*.log", "*.txt"):
            for f in path.rglob(pattern):
                messages.extend(self._read_file(f))
        return messages

    def _read_file(self, path: Path) -> List[str]:
        try:
            content = path.read_text(encoding="utf-8")
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            return lines
        except Exception as exc:
            logger.warning(f"Could not read {path}: {exc}")
            return []
