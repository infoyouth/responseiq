import argparse
import os
import sys
from pathlib import Path

from src.services.analyzer import analyze_message
from src.services.pr_service import PRService
from src.services.remediation_service import RemediationService
from src.utils.logger import logger

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


def scan_directory(target_path: str, mode: str):
    """
    Scans a directory for known issues.
    """
    logger.info(f"Starting ResponseIQ CLI in '{mode}' mode on '{target_path}'")

    path = Path(target_path)
    if not path.exists():
        logger.error(f"Target path {target_path} does not exist.")
        sys.exit(1)

    issues_found = []
    fixes_applied = 0

    # Determine files to scan
    files_to_scan = []
    # Files to ignore during recursive scan (to avoid false positives in configs/docs)
    IGNORED_EXTENSIONS = {
        ".yml",
        ".yaml",
        ".json",
        ".md",
        ".toml",
        ".pyc",
        ".pyo",
        ".lock",
    }

    if path.is_file():
        files_to_scan.append(path)
    else:
        for root, dirs, files in os.walk(path):
            for file in files:
                # Skip hidden files and venv
                if file.startswith(".") or "venv" in root:
                    continue

                # Check extension
                if Path(file).suffix.lower() in IGNORED_EXTENSIONS:
                    continue

                files_to_scan.append(Path(root) / file)

    for file_path in files_to_scan:
        try:
            # Read first 1KB to detect issues (simulation)
            msg = ""
            with open(file_path, "r", errors="ignore") as f:
                msg = f.read(1024)

            # Broaden detection for CLI to catch 'critical' and 'panic'
            msg_lower = msg.lower()
            detection_keywords = ["error", "fail", "exception", "panic", "critical"]

            if any(k in msg_lower for k in detection_keywords):
                logger.info(f"Analyzing potential issue in {file_path}")
                # Simulate result for demo if LLM not configured
                result = analyze_message(msg)

                # Fallback if analyzer missed keywords or severity is low
                # but we suspect it due to keywords
                if not result and "panic" in msg_lower:
                    result = {
                        "severity": "critical",
                        "reason": "System Panic Detected (Keyword)",
                    }

                if result and (
                    (result.get("severity") in ["high", "critical"])
                    or "panic" in msg_lower
                ):
                    # Force upgrade severity if panic present
                    if "panic" in msg_lower:
                        result["severity"] = "critical"

                    logger.warning(
                        f"Likely incident detected in {file_path}: {result['reason']}"
                    )

                    issue_record = {
                        "file": str(file_path),
                        "severity": result["severity"],
                        "context": msg.strip()[:200],
                        "reason": result.get("reason", "Unknown"),
                        "status": "Detected",
                    }

                    if mode == "fix":
                        logger.info("Fix mode enabled: Attempting remediation")
                        if attempt_fix(file_path, result):
                            fixes_applied += 1
                            issue_record["status"] = "Fixed"
                        else:
                            issue_record["status"] = "Fix Failed"

                    issues_found.append(issue_record)

        except Exception as e:
            logger.debug(f"Skipping {file_path}: {e}")

    write_summary(issues_found)
    logger.info(f"Scan complete. Found {len(issues_found)} issues.")

    if fixes_applied > 0:
        logger.info(f"Initiating batch PR creation for {fixes_applied} fixes...")
        pr_service.create_batch_pr(fixes_applied)

    if len(issues_found) > 0 and mode == "scan":
        sys.exit(1)  # Fail build on issues in scan mode


def attempt_fix(file_path: Path, issue: dict) -> bool:
    """
    Applies the physical fix locally using RemediationService.
    Does NOT create PRs directly.
    """
    logger.info(f"Attempting to remediate: {issue['reason']}")

    # 1. Apply Physical Fix (Static Analysis Engine)
    return remediation_service.remediate_incident(issue, file_path.parent)


def main():
    parser = argparse.ArgumentParser(description="ResponseIQ CLI")
    parser.add_argument("--target", default=".", help="Directory to scan")
    parser.add_argument(
        "--mode", default="scan", choices=["scan", "fix"], help="Operation mode"
    )
    # Support for GitHub Action inputs
    parser.add_argument("--action", choices=["scan", "fix"], help="Alias for --mode")
    parser.add_argument(
        "--url", help="Repository URL (e.g., https://github.com/owner/repo)"
    )
    parser.add_argument("--token", help="GitHub Token")

    # Ignored args that might be passed by action.yml but handled via ENV
    parser.add_argument("--github-token", help=argparse.SUPPRESS)
    parser.add_argument("--openai-api-key", help=argparse.SUPPRESS)

    args, unknown = parser.parse_known_args()

    # Map Action inputs to CLI args
    mode = args.action if args.action else args.mode

    # Set Env vars from args if provided
    if args.token:
        os.environ["GITHUB_TOKEN"] = args.token
    if args.url:
        # Extract owner/repo from URL if possible, or use as is if logic supports it
        # Expected format: https://github.com/owner/repo
        if "github.com/" in args.url:
            repo_slug = args.url.split("github.com/")[-1].replace(".git", "")
            os.environ["GITHUB_REPOSITORY"] = repo_slug

    scan_directory(args.target, mode)


if __name__ == "__main__":
    main()
