import asyncio
import json
from pathlib import Path
from typing import List

from loguru import logger

from .base import BasePlugin


class ScanPlugin(BasePlugin):
    def run(self, agent_state: dict) -> dict:
        agent_state = agent_state.copy()
        target = agent_state.get("context", {}).get("args", {}).get("target")

        if not target:
            agent_state["scan_result"] = "error"
            agent_state["scan_error"] = (
                "No --target specified. Use --target <file_or_directory> or --target - to read from stdin."
            )
            return agent_state

        # stdin pipe mode: responseiq --mode scan --target -
        if target == "-":
            messages = self._filter_noise_lines(self._read_stdin())
        else:
            target_path = Path(target)
            if not target_path.exists():
                agent_state["scan_result"] = "error"
                agent_state["scan_error"] = f"Target not found: {target}"
                return agent_state
            messages = self._collect_messages(target_path)

        if not messages:
            agent_state["scan_result"] = "no_incidents"
            agent_state["incidents"] = []
            agent_state["total_scanned"] = 0
            return agent_state

        from responseiq.services.analyzer import analyze_log_async

        # Run all analyses in a single event loop via gather — calling asyncio.run()
        # once per message creates/destroys a loop each iteration, which causes the
        # httpx connection pool to emit "RuntimeError: Event loop is closed" noise
        # during its background cleanup tasks.
        async def _run_all(msgs: List[str]):
            return await asyncio.gather(*[analyze_log_async(m) for m in msgs])

        results = asyncio.run(_run_all(messages))
        incidents = [r.model_dump() for r in results if r is not None]

        agent_state["scan_result"] = "success"
        agent_state["incidents"] = incidents
        agent_state["total_scanned"] = len(messages)
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
            if path.suffix == ".json":
                data = json.loads(content)
                if isinstance(data, dict) and "message" in data:
                    return [data["message"]]
                if isinstance(data, list):
                    return [item["message"] for item in data if isinstance(item, dict) and "message" in item]
            else:
                # Plain log — filter noise then analyse each non-empty line, cap at 50
                raw = [line.strip() for line in content.splitlines() if line.strip()]
                return self._filter_noise_lines(raw)[:50]
        except Exception as exc:
            logger.warning("Failed to read %s: %s", path, exc)
        return []
