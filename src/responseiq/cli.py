import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from responseiq.__version__ import __version__
from responseiq.schemas.incident import Incident, IncidentSeverity, LogEntry
from responseiq.services.analyzer import analyze_message_async
from responseiq.services.impact import assess_impact
from responseiq.services.pr_service import PRService
from responseiq.services.remediation_service import RemediationService
from responseiq.services.shadow_analytics import ShadowAnalyticsService
from responseiq.utils.config_loader import load_config
from responseiq.utils.logger import logger

# Initialize Services
remediation_service = RemediationService()
pr_service = PRService()
shadow_analytics = ShadowAnalyticsService()  # P2.1 Shadow Mode


def write_summary(issues: list):
    """
    Writes a Markdown summary to GITHUB_STEP_SUMMARY.
    """
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    with open(summary_file, "a") as f:
        f.write("# 🔍 ResponseIQ Scan Results\n\n")
        if not issues:
            f.write("✅ **No critical issues found.**\n")
            return

        f.write(f"⚠️ Found **{len(issues)}** potential issues:\n\n")
        f.write("| Severity | File | Reason | Action |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")

        for issue in issues:
            sev_icon = "🔴" if issue["severity"] == "critical" else "🟠"
            file_name = Path(issue["file"]).name
            f.write(
                f"| {sev_icon} {issue['severity'].upper()} | `{file_name}` | "
                f"{issue['reason']} | {issue['status']} |\n"
            )

        f.write("\n_Analysis performed by ResponseIQ_\n")


async def process_file(file_path: Path, mode: str) -> Optional[dict]:
    """
    Async worker to process a single file.
    Uses Parallel Log Processing for large files.
    """
    try:
        msg = ""
        # Advanced: Use ParallelLogProcessor if file is large (>1MB) logic is inside
        from responseiq.utils.log_processor import ParallelLogProcessor

        processor = ParallelLogProcessor()

        # This will auto-switch between "fast read" and "parallel map-reduce"
        msg = await processor.scan_large_file(file_path)

        if not msg:
            return None

        msg_lower = msg.lower()
        detection_keywords = ["error", "fail", "exception", "panic", "critical"]

        if any(k in msg_lower for k in detection_keywords):
            logger.info(f"Analyzing potential issue in {file_path}")

            # Use async analyzer
            result = await analyze_message_async(msg)

            # Fallback if analyzer missed keywords or severity is low
            if not result and "panic" in msg_lower:
                result = {
                    "severity": "critical",
                    "reason": "System Panic Detected (Keyword)",
                }

            if result and ((result.get("severity") in ["high", "critical"]) or "panic" in msg_lower):
                if "panic" in msg_lower:
                    result["severity"] = "critical"

                logger.warning(f"Likely incident detected in {file_path}: {result['reason']}")

                issue_record = {
                    "file": str(file_path),
                    "severity": result["severity"],
                    "context": msg.strip()[:200],
                    "reason": result.get("reason", "Unknown"),
                    "status": "Detected",
                }

                impact = assess_impact(
                    severity=result.get("severity"),
                    title=result.get("reason"),
                    description=msg.strip()[:200],
                    source=result.get("source"),
                )
                issue_record["impact_score"] = impact.score
                issue_record["impact_factors"] = impact.factors

                if mode == "fix":
                    logger.info("Fix mode enabled: Attempting remediation")
                    if await attempt_fix(file_path, result):
                        issue_record["status"] = "Fixed"
                    else:
                        issue_record["status"] = "Fix Failed"

                return issue_record
    except Exception as e:
        logger.debug(f"Skipping {file_path}: {e}")

    return None


async def scan_directory_async(target_path: str, mode: str):
    """
    Scans a directory for known issues using async concurrency.
    """
    logger.info(f"Starting ResponseIQ CLI in '{mode}' mode on '{target_path}'")

    path = Path(target_path)
    if not path.exists():
        logger.error(f"Target path {target_path} does not exist.")
        sys.exit(1)

    # Load Configuration (User defined or Defaults)
    config = load_config(Path.cwd())

    # Determine files to scan
    files_to_scan = []

    if path.is_file():
        files_to_scan.append(path)
    else:
        for root, dirs, files in os.walk(path):
            # Prune directories in-place using config
            # We specifically filter out ignored dirs to improve performance logic
            dirs[:] = [d for d in dirs if d not in config.ignored_dirs and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                if config.is_ignored(file_path):
                    continue
                files_to_scan.append(file_path)

    if not files_to_scan:
        logger.warning(
            f"No relevant log files found in '{target_path}'. (Check your ignore settings in pyproject.toml)"
        )
        return

    # Create tasks for all files
    tasks = [process_file(f, mode) for f in files_to_scan]

    # Run them concurrently
    results = await asyncio.gather(*tasks)

    # Filter out None results
    issues_found = [r for r in results if r is not None]
    issues_found.sort(key=lambda current: current.get("impact_score", 0.0), reverse=True)

    write_summary(issues_found)
    logger.info(f"Scan complete. Found {len(issues_found)} issues.")

    fixes_applied = sum(1 for i in issues_found if i["status"] == "Fixed")

    if fixes_applied > 0:
        logger.info(f"Initiating batch PR creation for {fixes_applied} fixes...")
        pr_service.create_batch_pr(fixes_applied)

    if len(issues_found) > 0 and mode == "scan":
        sys.exit(1)


async def run_shadow_mode(target_path: str, args):
    """
    P2.1 Shadow Mode: Analyze incidents without applying fixes.
    Provides management value and ROI projections with zero risk.
    """
    logger.info(f"🔍 Starting ResponseIQ P2.1 Shadow Mode on '{target_path}'")

    path = Path(target_path)
    if not path.exists():
        logger.error(f"Target path {target_path} does not exist.")
        sys.exit(1)

    # Load Configuration
    config = load_config(Path.cwd())

    # Create mock incidents from log files for shadow analysis
    incidents = await create_incidents_from_logs(path, config)

    if not incidents:
        logger.warning(f"No incidents created from '{target_path}' for shadow analysis.")
        return

    logger.info(f"Created {len(incidents)} incidents for shadow analysis")

    # Run shadow analytics
    shadow_results = []
    for incident in incidents:
        logger.info(f"📊 Shadow analyzing: {incident.title}")
        result = await shadow_analytics.analyze_incident_shadow(incident)
        shadow_results.append(result)

        print(f"   Confidence: {result.confidence_score:.1%}")
        print(f"   Fix Time: {result.projected_fix_time_minutes}min")
        print(f"   Value Score: {result.value_score}/10")
        print(f"   Risk: {result.risk_assessment}")

    # Generate management report if requested
    if args.shadow_report:
        await generate_shadow_report(shadow_results, args)

    # Output results in requested format
    output_shadow_results(shadow_results, args.shadow_format)

    logger.info("🎯 Shadow analysis complete - no fixes applied, zero risk")


async def create_incidents_from_logs(path: Path, config) -> list[Incident]:
    """Convert log files into incident objects for shadow analysis."""
    incidents = []

    # Get log files
    files_to_scan = []
    if path.is_file():
        files_to_scan.append(path)
    else:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in config.ignored_dirs and not d.startswith(".")]
            for file in files:
                file_path = Path(root) / file
                if not config.is_ignored(file_path):
                    files_to_scan.append(file_path)

    # Process files and create incidents
    incident_id = 1
    for file_path in files_to_scan[:10]:  # Limit to 10 files for demo
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.strip().split("\n")

            # Create incident from file content
            if lines:
                incident = Incident(
                    id=f"INC-SHADOW-{incident_id:03d}",
                    title=f"Log Analysis: {file_path.name}",
                    description=f"Shadow analysis of log file {file_path}",
                    severity=IncidentSeverity.MEDIUM,
                    service=file_path.stem,
                    logs=[
                        LogEntry(
                            timestamp=datetime.now(),
                            level="INFO",
                            service=file_path.stem,
                            message=line[:500],  # Truncate long lines
                        )
                        for line in lines[:5]
                        if line.strip()  # Take first 5 non-empty lines
                    ],
                    tags=["shadow", "log-analysis", file_path.suffix[1:] if file_path.suffix else "text"],
                    created_at=datetime.now(),
                    resolved_at=None,
                    source_repo=f"file://{file_path.absolute()}",
                )
                incidents.append(incident)
                incident_id += 1

        except Exception as e:
            logger.debug(f"Skipping {file_path}: {e}")

    return incidents


async def generate_shadow_report(shadow_results, args):
    """Generate management report from shadow analysis results."""
    logger.info("📈 Generating management value report...")

    # Generate period report
    period_report = await shadow_analytics.generate_period_report(
        start_date=datetime.now() - timedelta(days=args.shadow_days), end_date=datetime.now()
    )

    # Save report based on format
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.shadow_format == "json":
        report_file = f"shadow_report_{timestamp}.json"
        report_data = {
            "period_report": period_report.dict(),
            "shadow_results": [r.dict() for r in shadow_results],
            "generated_at": datetime.now().isoformat(),
        }
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        logger.info(f"📄 JSON report saved: {report_file}")

    elif args.shadow_format == "executive":
        # Executive summary format
        report_file = f"executive_summary_{timestamp}.md"
        with open(report_file, "w") as f:
            f.write("# ResponseIQ Shadow Analysis - Executive Summary\n\n")
            f.write(f"**Analysis Period:** {args.shadow_days} days\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Key Metrics\n\n")
            f.write(f"- **Incidents Analyzed:** {period_report.total_incidents}\n")
            f.write(f"- **Automation Candidates:** {period_report.automation_candidates}\n")
            f.write(f"- **Projected Annual Savings:** ${period_report.projected_annual_savings:,.2f}\n")
            f.write(f"- **Average Time Saved:** {period_report.avg_time_saved_minutes} minutes per incident\n")
            f.write(f"- **ROI Projection:** {period_report.roi_projection:.1%}\n\n")
            f.write("## Recommendation\n\n")
            if period_report.roi_projection > 0.3:
                f.write("✅ **High Value**: Immediate deployment recommended for maximum ROI\n")
            elif period_report.roi_projection > 0.1:
                f.write("⚠️ **Medium Value**: Pilot deployment recommended\n")
            else:
                f.write("❌ **Low Value**: Further analysis required\n")
        logger.info(f"📄 Executive summary saved: {report_file}")

    else:  # markdown (default)
        report_file = f"shadow_report_{timestamp}.md"
        with open(report_file, "w") as f:
            f.write("# ResponseIQ P2.1 Shadow Analysis Report\n\n")
            f.write(f"**Analysis Period:** {args.shadow_days} days  \n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n")
            f.write("## Management Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Total Incidents | {period_report.total_incidents} |\n")
            f.write(f"| Automation Candidates | {period_report.automation_candidates} |\n")
            f.write(f"| Projected Annual Savings | ${period_report.projected_annual_savings:,.2f} |\n")
            f.write(f"| Average Time Saved | {period_report.avg_time_saved_minutes} minutes |\n")
            f.write(f"| ROI Projection | {period_report.roi_projection:.1%} |\n\n")
            f.write("## Shadow Analysis Results\n\n")
            for i, result in enumerate(shadow_results, 1):
                f.write(f"### Incident {i}\n")
                f.write(f"- **Confidence:** {result.confidence_score:.1%}\n")
                f.write(f"- **Fix Time:** {result.projected_fix_time_minutes} minutes\n")
                f.write(f"- **Value Score:** {result.value_score}/10\n")
                f.write(f"- **Risk Assessment:** {result.risk_assessment}\n\n")
        logger.info(f"📄 Markdown report saved: {report_file}")


def output_shadow_results(shadow_results, format_type):
    """Output shadow analysis results to console."""
    if format_type == "json":
        print(json.dumps([r.dict() for r in shadow_results], indent=2, default=str))
    else:
        print("\n🔍 SHADOW ANALYSIS SUMMARY:")
        print("=" * 50)
        total_incidents = len(shadow_results)
        avg_confidence = sum(r.confidence_score for r in shadow_results) / total_incidents if total_incidents > 0 else 0
        avg_fix_time = (
            sum(r.projected_fix_time_minutes for r in shadow_results) / total_incidents if total_incidents > 0 else 0
        )
        avg_value = sum(r.value_score for r in shadow_results) / total_incidents if total_incidents > 0 else 0

        print(f"Total Incidents Analyzed: {total_incidents}")
        print(f"Average Confidence Score: {avg_confidence:.1%}")
        print(f"Average Projected Fix Time: {avg_fix_time:.1f} minutes")
        print(f"Average Value Score: {avg_value:.1f}/10")

        high_confidence = sum(1 for r in shadow_results if r.confidence_score > 0.8)
        print(f"High Confidence Fixes: {high_confidence} ({high_confidence/total_incidents:.1%})")


async def attempt_fix(file_path: Path, issue: dict) -> bool:
    """
    Applies the physical fix locally using RemediationService.
    Does NOT create PRs directly.
    """
    logger.info(f"Attempting to remediate: {issue['reason']}")

    # 1. Apply Physical Fix (Static Analysis Engine)
    recommendation = await remediation_service.remediate_incident(issue, file_path.parent)
    return recommendation.allowed


def main():
    parser = argparse.ArgumentParser(description="ResponseIQ CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--target", default=None, help="Directory to scan (defaults to './logs' if exists)")
    parser.add_argument("--mode", default="scan", choices=["scan", "fix", "shadow"], help="Operation mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

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

    # Configure Logging based on flag
    log_level = "DEBUG" if args.debug else "INFO"
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
    )

    # Map Action inputs to CLI args
    mode = args.action if args.action else args.mode

    # Handle shadow mode flag
    if args.shadow_mode or args.shadow_report:
        mode = "shadow"

    # Set Env vars from args if provided
    if args.token:
        os.environ["GITHUB_TOKEN"] = args.token
    if args.url:
        if "github.com/" in args.url:
            repo_slug = args.url.split("github.com/")[-1].replace(".git", "")
            os.environ["GITHUB_REPOSITORY"] = repo_slug

    # Smart Target Resolution
    target_path = args.target
    if target_path is None:
        if Path("./logs").exists() and Path("./logs").is_dir():
            target_path = "./logs"
            logger.info("No target specified. Auto-detected './logs' directory.")
        else:
            # Print help + banner
            parser.print_help()
            print()  # Spacer
            logger.warning("No target specified and no './logs' folder found.")
            logger.warning("Please provide a path (e.g., 'responseiq --target ./var/log')")
            sys.exit(0)

    try:
        if mode == "shadow":
            asyncio.run(run_shadow_mode(target_path, args))
        else:
            asyncio.run(scan_directory_async(target_path, mode))
    except KeyboardInterrupt:
        logger.info("Scan cancelled by user.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
