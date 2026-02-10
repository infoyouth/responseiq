import argparse
import os
import sys
from pathlib import Path

from src.integrations.github_integration import GitHubIntegration
from src.services.analyzer import analyze_message
from src.utils.logger import logger


def scan_directory(target_path: str, mode: str):
    """
    Scans a directory for known issues.
    """
    logger.info(f"Starting ResponseIQ CLI in '{mode}' mode on '{target_path}'")

    path = Path(target_path)
    if not path.exists():
        logger.error(f"Target path {target_path} does not exist.")
        sys.exit(1)

    # Simple walk for MVP
    issues_found = 0
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

                # Analyze
                if (
                    "error" in msg.lower()
                    or "fail" in msg.lower()
                    or "exception" in msg.lower()
                ):
                    logger.info(f"Analyzing potential issue in {file_path}")
                    # Simulate result for demo if LLM not configured
                    result = analyze_message(msg)

                    if result and result.get("severity") in ["high", "critical"]:
                        logger.warning(
                            f"Likely incident detected in {file}: {result['reason']}"
                        )
                        issues_found += 1

                        if mode == "fix":
                            logger.info(
                                "Fix mode enabled: Attempting remediation (simulation)"
                            )
                            attempt_fix(file_path, result)
            except Exception as e:
                logger.debug(f"Skipping {file}: {e}")

    logger.info(f"Scan complete. Found {issues_found} issues.")
    if issues_found > 0 and mode == "scan":
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
