import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from responseiq.__version__ import __version__
from responseiq.services.analyzer import analyze_message_async
from responseiq.services.impact import assess_impact
from responseiq.services.pr_service import PRService
from responseiq.services.remediation_service import RemediationService
from responseiq.utils.config_loader import load_config
from responseiq.utils.logger import logger

# Initialize Services
remediation_service = RemediationService()
pr_service = PRService()


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


async def attempt_fix(file_path: Path, issue: dict) -> bool:
    """
    Applies the physical fix locally using RemediationService.
    Does NOT create PRs directly.
    """
    logger.info(f"Attempting to remediate: {issue['reason']}")

    # 1. Apply Physical Fix (Static Analysis Engine)
    return await remediation_service.remediate_incident(issue, file_path.parent)


def main():
    parser = argparse.ArgumentParser(description="ResponseIQ CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--target", default=None, help="Directory to scan (defaults to './logs' if exists)")
    parser.add_argument("--mode", default="scan", choices=["scan", "fix"], help="Operation mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    # Support for GitHub Action inputs
    parser.add_argument("--action", choices=["scan", "fix"], help="Alias for --mode")
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
        asyncio.run(scan_directory_async(target_path, mode))
    except KeyboardInterrupt:
        logger.info("Scan cancelled by user.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
