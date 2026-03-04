import argparse
import os
import sys

from responseiq.__version__ import __version__
from responseiq.models.agent_state import AgentState
from responseiq.plugin_registry import PluginRegistry
from responseiq.telemetry import ConsoleTelemetry

telemetry = ConsoleTelemetry()


def main():
    parser = argparse.ArgumentParser(description="ResponseIQ CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--target", default=None, help="Directory to scan (defaults to './logs' if exists)")
    parser.add_argument("--mode", default="scan", choices=["scan", "fix", "shadow"], help="Operation mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (shortcut for --log-level DEBUG)")
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set log level (default: WARNING; use --debug for DEBUG)",
    )

    # P2.1 Shadow Analytics Arguments
    parser.add_argument("--shadow-mode", action="store_true", help="Run shadow analysis without applying fixes")
    parser.add_argument("--shadow-report", action="store_true", help="Generate management value report")
    parser.add_argument("--shadow-days", type=int, default=7, help="Days to include in shadow report (default: 7)")
    parser.add_argument(
        "--shadow-format",
        choices=["json", "markdown", "executive"],
        default="markdown",
        help="Shadow report output format",
    )

    # Support for GitHub Action inputs
    parser.add_argument("--action", choices=["scan", "fix", "shadow"], help="Alias for --mode")
    parser.add_argument("--url", help="Repository URL (e.g., https://github.com/owner/repo)")
    parser.add_argument("--token", help="GitHub Token")

    # Ignored args that might be passed by action.yml but handled via ENV
    parser.add_argument("--github-token", help=argparse.SUPPRESS)
    parser.add_argument("--openai-api-key", help=argparse.SUPPRESS)

    args, unknown = parser.parse_known_args()

    # Determine log level: --debug > --log-level > default WARNING
    log_level = "DEBUG" if args.debug else (args.log_level or "WARNING")
    import logging

    logging.basicConfig(
        stream=sys.stderr,
        level=getattr(logging, log_level),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    # Map Action inputs to CLI args
    mode = args.action if args.action else args.mode
    if args.shadow_mode or args.shadow_report:
        mode = "shadow"

    # Set Env vars from args if provided
    if args.token:
        os.environ["GITHUB_TOKEN"] = args.token
    if args.url:
        if "github.com/" in args.url:
            repo_slug = args.url.split("github.com/")[-1].replace(".git", "")
            os.environ["GITHUB_REPOSITORY"] = repo_slug

    # Initialize AgentState with global context and trace_id
    trace_id = os.environ.get("TRACEPARENT") or os.environ.get("TRACE_ID")
    agent_state: AgentState = {
        "context": {
            "args": vars(args),
            "env": dict(os.environ),
        },
        "trace_id": trace_id,
    }

    # Plugin loading and execution
    registry = PluginRegistry()
    if mode not in registry.plugins:
        print(f"Unknown command: {mode}", file=sys.stderr)
        sys.exit(1)
    plugin_cls = registry.get_plugin(mode)
    plugin = plugin_cls()
    try:
        updated_state = plugin.run(agent_state)
        _print_result(mode, updated_state)
        sys.exit(0)
    except Exception as e:
        telemetry.emit_event("PluginError", {"plugin": mode, "error": str(e)})
        print(f"Error running plugin {mode}: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Human-readable output formatter
# ---------------------------------------------------------------------------

_SEVERITY_ICON = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]   ",
    "medium": "[MEDIUM] ",
    "low": "[LOW]    ",
    "info": "[INFO]   ",
}


def _print_result(mode: str, state: dict) -> None:
    """Render a clean, human-readable summary to stdout."""
    sep = "-" * 60

    if mode == "scan":
        result = state.get("scan_result", "unknown")
        error = state.get("scan_error")
        incidents = state.get("incidents", [])
        total = state.get("total_scanned", 0)
        target = state.get("context", {}).get("args", {}).get("target", "unknown")

        print(sep)
        print("  ResponseIQ Scan Report")
        print(f"  Target : {target}")
        print(f"  Status : {result.upper()}")
        print(sep)

        if error:
            print(f"  ERROR: {error}")
            print(sep)
            return

        if not incidents:
            print("  No incidents detected.")
            print(sep)
            return

        print(f"  Scanned  : {total} message(s)")
        print(f"  Incidents: {len(incidents)} found")
        print(sep)

        for i, inc in enumerate(incidents, 1):
            severity = (inc.get("severity") or "unknown").lower()
            icon = _SEVERITY_ICON.get(severity, f"[{severity.upper()[:6]}]")
            title = inc.get("title") or "Untitled Incident"
            description = inc.get("description") or ""
            source = inc.get("source") or "unknown"
            impact = inc.get("impact_score")

            print(f"  {i}. {icon} {title}")
            print(f"     Source     : {source}")
            if impact is not None:
                print(f"     Impact     : {impact:.1f}/100")
            if description:
                # Wrap long descriptions
                words = description.split()
                line: list[str] = []
                lines: list[str] = []
                for w in words:
                    if sum(len(x) + 1 for x in line) + len(w) > 70:
                        lines.append(" ".join(line))
                        line = [w]
                    else:
                        line.append(w)
                if line:
                    lines.append(" ".join(line))
                print(f"     Description: {lines[0]}")
                for line_part in lines[1:]:
                    print(f"                  {line_part}")
            remediation = inc.get("remediation")
            if remediation:
                print(f"     Fix        : {remediation[:120]}")
            print()

        print(sep)
        print("  Tip: run with --mode fix to apply safe remediations.")
        print(sep)

    elif mode == "fix":
        print(sep)
        print("  ResponseIQ Fix Report")
        print(sep)
        for k, v in state.items():
            if k not in ("context", "trace_id") and v is not None:
                print(f"  {k}: {v}")
        print(sep)

    else:
        # Shadow or unknown — print non-env keys
        print(sep)
        print(f"  ResponseIQ {mode.title()} Report")
        print(sep)
        for k, v in state.items():
            if k not in ("context", "trace_id") and v is not None:
                print(f"  {k}: {v}")
        print(sep)


if __name__ == "__main__":
    main()
