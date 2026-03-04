import asyncio
import json
from pathlib import Path
from typing import List

from .base import BasePlugin


class ScanPlugin(BasePlugin):
    def run(self, agent_state: dict) -> dict:
        agent_state = agent_state.copy()
        target = agent_state.get("context", {}).get("args", {}).get("target")

        if not target:
            agent_state["scan_result"] = "error"
            agent_state["scan_error"] = "No --target specified. Use --target <file_or_directory>"
            return agent_state

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

        incidents = []
        for msg in messages:
            result = asyncio.run(analyze_log_async(msg))
            if result:
                incidents.append(result.model_dump())

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
                # Plain log — analyse each non-empty line, cap at 50
                return [line.strip() for line in content.splitlines() if line.strip()][:50]
        except Exception:
            pass
        return []
