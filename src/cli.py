import argparse
import os
import sys
from pathlib import Path

from src.integrations.github_integration import GitHubIntegration
from src.services.analyzer import analyze_message
from src.utils.logger import logger


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
            sev_icon = "🔴" if issue['severity'] == "critical" else "🟠"
            file_name = issue['path'].name
            f.write(f"| {sev_icon} {issue['severity'].upper()} | `{file_name}` | {issue['reason']} | {issue['status']} |\n")
        
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
    
    # Simple walk for MVP
    for root, dirs, files in os.walk(path):
        for file in files:
            # Skip hidden files and venv
            if file.startswith(".") or "venv" in root:
                continue

            file_path = Path(root) / file
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

                    # Fallback if analyzer didn't catch matched keyword or severity is too low
                    # but we strongly suspect it due to keywords
                    if not result and "panic" in msg_lower:
                         result = {"severity": "critical", "reason": "System Panic Detected (Keyword)"}
                    
                    if result and ((result.get("severity") in ["high", "critical"]) or "panic" in msg_lower):
                         # Force upgrade severity if panic present
                         if "panic" in msg_lower:
                             result["severity"] = "critical"
                             
                         logger.warning(
                            f"Likely incident detected in {file}: {result['reason']}"
                        )
                        
                         issue_record = {
                            "severity": result.get("severity", "high"),
                            "path": file_path,
                            "reason": result.get("reason"),
                            "status": "Reported"
                        }

                        if mode == "fix":
                            logger.info(
                                "Fix mode enabled: Attempting remediation (simulation)"
                            )
                            attempt_fix(file_path, result)
                            issue_record["status"] = "Fix Attempted"

                        issues_found.append(issue_record)

            except Exception as e:
                logger.debug(f"Skipping {file}: {e}")

    write_summary(issues_found)
    logger.info(f"Scan complete. Found {len(issues_found)} issues.")
    
    if len(issues_found) > 0 and mode == "scan":
        sys.exit(1)  # Fail build on issues in scan mode


def attempt_fix(file_path: Path, issue: dict):
    """
    Simulates a fix action via GitHub PR.
    """
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_name:
        logger.warning(
            "Not running in GitHub Actions (GITHUB_REPOSITORY missing). "
            "Cannot create PR."
        )
        return

    gh = GitHubIntegration()
    if not gh.check_permissions():
        logger.error("GitHub permissions check failed.")
        return

    # Create PR logic simulation
    title = f"fix: Resolve {issue.get('reason')} in {file_path.name}"
    # gh.create_pr(...)
    logger.info(f"Would create PR on {repo_name} with title: {title}")


def main():
    parser = argparse.ArgumentParser(description="ResponseIQ CLI")
    parser.add_argument("--target", default=".", help="Directory to scan")
    parser.add_argument(
        "--mode", default="scan", choices=["scan", "fix"], help="Operation mode"
    )

    # Ignored args that might be passed by action.yml but handled via ENV
    parser.add_argument("--github-token", help=argparse.SUPPRESS)
    parser.add_argument("--openai-api-key", help=argparse.SUPPRESS)

    args, unknown = parser.parse_known_args()

    scan_directory(args.target, args.mode)


if __name__ == "__main__":
    main()
