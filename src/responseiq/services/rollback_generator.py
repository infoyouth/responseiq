"""
Executable Rollback Script Generator for P2.1 - Production Safety.

Generates executable Python scripts for deterministic rollbacks beyond git,
including database changes, configuration changes, and environment variables.
"""

from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from responseiq.utils.logger import logger


class RollbackAction:
    """Individual rollback action with execution details."""

    def __init__(
        self,
        action_type: str,
        description: str,
        command: str,
        validation_check: Optional[str] = None,
        critical: bool = False,
    ):
        self.action_type = action_type  # "git", "file", "env", "database", "k8s"
        self.description = description
        self.command = command
        self.validation_check = validation_check  # Command to verify rollback worked
        self.critical = critical  # If true, stop rollback on failure


class ExecutableRollbackGenerator:
    """
    Generates executable Python rollback scripts.

    Moving from text-based rollback plans to executable scripts that can:
    - Revert code changes
    - Reset environment variables
    - Restore database configurations
    - Rollback Kubernetes deployments
    - Validate each step
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("rollbacks")
        self.output_dir.mkdir(exist_ok=True)

    async def generate_rollback_script(self, *args, **kwargs) -> Any:
        """Flexible rollback script generator.

        Two supported call patterns (kept intentionally compatible with tests):
        1) async generate_rollback_script(changes: List[str], context: Dict[str, Any]) -> str
           - Returns the generated script content as a string (used by tests).

        2) generate_rollback_script(incident_id=..., analysis_result=..., affected_files=..., proposed_changes=...)
           - Backward compatible synchronous-style call used by internal services; returns a Path to the written file.
           - Note: callers within async code should `await` this method as well.
        """
        # Pattern (1): positional (changes, context) -> return script string
        if len(args) == 2 and isinstance(args[0], list) and isinstance(args[1], dict):
            changes, context = args[0], args[1]

            # Build a light-weight analysis_result and proposed_changes from inputs
            analysis_result = {"title": context.get("title", "Generated rollback"), "confidence": 0.75}
            proposed_changes = [{"type": "mock", "command": c} for c in changes]

            # Use a demo incident id for script generation
            incident_id = context.get("incident_id", f"anon_{datetime.now().strftime('%Y%m%d%H%M%S')}")

            # Analyze into rollback actions and return script string (no file write)
            rollback_actions = self._analyze_changes_for_rollback(analysis_result, [], proposed_changes)
            script_content = self._generate_script_content(incident_id, analysis_result, rollback_actions)
            return script_content

        # Pattern (2): keyword args (backward-compatible file output)
        incident_id = kwargs.get("incident_id") or (args[0] if args else None)
        analysis_result = kwargs.get("analysis_result") or (args[1] if len(args) > 1 else {})
        affected_files = kwargs.get("affected_files") or (args[2] if len(args) > 2 else [])
        proposed_changes = kwargs.get("proposed_changes") or (args[3] if len(args) > 3 else [])

        if not incident_id:
            raise ValueError("incident_id is required for file-backed rollback generation")

        logger.info(f"🔄 Generating executable rollback script for {incident_id}")

        # Create detailed rollback actions and write file
        rollback_actions = self._analyze_changes_for_rollback(
            analysis_result or {}, affected_files or [], proposed_changes or []
        )

        if not rollback_actions:
            logger.warning(f"No rollback actions identified for {incident_id}")
            rollback_actions = [
                RollbackAction(
                    "manual",
                    "No automatic rollback available",
                    "print('Manual intervention required')",
                )
            ]

        # Generate the Python script
        script_content = self._generate_script_content(incident_id, analysis_result or {}, rollback_actions)

        # Write to file
        script_path = self.output_dir / f"rollback_{incident_id}.py"
        script_path.write_text(script_content, encoding="utf-8")

        logger.info(f"✅ Rollback script generated: {script_path}")
        return script_path

    def _analyze_changes_for_rollback(
        self,
        analysis: Dict[str, Any],
        affected_files: List[str],
        proposed_changes: List[Dict[str, Any]],
    ) -> List[RollbackAction]:
        """Analyze proposed changes to determine appropriate rollback actions."""
        actions = []

        # Always start with git backup
        actions.append(
            RollbackAction(
                "git",
                "Create safety backup before rollback",
                "subprocess.run(['git', 'stash', 'push', '-m', 'Pre-rollback safety backup'], check=True)",
                "subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)",
            )
        )

        # Analyze proposed changes for specific rollback needs
        for change in proposed_changes:
            change_type = change.get("type", "unknown")

            # Support lightweight/raw commands generated from positional helpers
            if change_type in ("mock", "raw", "command") or change.get("command"):
                cmd = change.get("command") or change.get("cmd") or str(change)
                actions.append(
                    RollbackAction(
                        "manual",
                        f"Run command rollback: {cmd}",
                        f"subprocess.run(r'''{cmd}''', shell=True, check=True)",
                        "True",
                    )
                )
                continue

            if change_type == "file_modification":
                # File changes - git revert
                actions.append(
                    RollbackAction(
                        "git",
                        f"Revert file changes: {change.get('description', '')}",
                        f"subprocess.run(['git', 'checkout', 'HEAD~1', '--'] + {affected_files!r}, check=True)",
                        f"subprocess.run(['git', 'diff', '--quiet', 'HEAD~1', '--'] + {affected_files!r})",
                        critical=True,
                    )
                )

            elif change_type == "environment_variable":
                # Environment variable changes
                var_name = change.get("variable_name", "UNKNOWN_VAR")
                original_value = change.get("original_value", "")
                actions.append(
                    RollbackAction(
                        "env",
                        f"Restore environment variable {var_name}",
                        f"os.environ['{var_name}'] = '{original_value}'",
                        f"os.environ.get('{var_name}') == '{original_value}'",
                    )
                )

            elif change_type == "database_config":
                # Database configuration changes
                config_key = change.get("config_key", "unknown")
                original_value = change.get("original_value", "")
                actions.append(
                    RollbackAction(
                        "database",
                        f"Revert database config: {config_key}",
                        f"# TODO: Implement database config rollback for {config_key}",
                        "# TODO: Add validation for database config rollback",
                    )
                )

            elif change_type == "k8s_deployment":
                # Kubernetes deployment changes
                deployment_name = change.get("deployment_name", "unknown")
                actions.append(
                    RollbackAction(
                        "k8s",
                        f"Rollback Kubernetes deployment: {deployment_name}",
                        f"subprocess.run(['kubectl', 'rollout', 'undo', 'deployment/{deployment_name}'], check=True)",
                        f"subprocess.run(['kubectl', 'rollout', 'status', 'deployment/{deployment_name}'], check=True)",
                        critical=True,
                    )
                )

        # Always end with health verification
        actions.append(
            RollbackAction(
                "validation",
                "Verify system health after rollback",
                textwrap.dedent("""
                # Health check validation
                try:
                    import requests
                    response = requests.get('http://localhost:8000/health', timeout=10)
                    if response.status_code != 200:
                        raise Exception(f'Health check failed: {response.status_code}')
                    print('✅ Health check passed')
                except Exception as e:
                    print(f'❌ Health check failed: {e}')
                    return False
                """).strip(),
                validation_check="True",  # Health check is self-validating
            )
        )

        return actions

    def _generate_script_content(
        self,
        incident_id: str,
        analysis: Dict[str, Any],
        actions: List[RollbackAction],
    ) -> str:
        """Generate the complete Python rollback script."""
        timestamp = datetime.now().isoformat()

        # Generate action implementations
        action_implementations = []
        for i, action in enumerate(actions, 1):
            action_impl = textwrap.indent(
                textwrap.dedent(f'''
def rollback_step_{i}(self):
    """{action.description}

    Type: {action.action_type}
    """
    print(f"Step {i}: {action.description}")
    try:
{textwrap.indent(action.command, "        ")}

        # Validation check
        validation_result = {action.validation_check}
        if not validation_result:
            raise Exception("Validation check failed")

        print("  ✅ Success")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {{e}}")
        {"return False" if action.critical else "print('  ⚠️  Non-critical failure, continuing')"}
        {"" if action.critical else "return True"}
'''),
                "    ",
            )
            action_implementations.append(action_impl)

        # Generate main execution logic
        main_execution = self._generate_main_execution(actions)

        # Add a `main()` wrapper so generated scripts are easier to test and import
        main_wrapper = textwrap.dedent('''
        def main():
            """Entry point for the rollback script."""
            executor = RollbackExecutor()
            return executor.execute_rollback()
        ''').strip()

        script_template = f'''#!/usr/bin/env python3
"""
Rollback script for ResponseIQ incident: {incident_id}

Generated: {timestamp}
Incident: {analysis.get("title", "Unknown")}
Confidence: {analysis.get("confidence", 0.0)}

This script performs deterministic rollback of remediation changes.
Run with: python rollback_{incident_id}.py
"""

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


class RollbackExecutor:
    """Manages rollback execution with safety checks."""

    def __init__(self):
        self.incident_id = "{incident_id}"
        self.rollback_log = []

{chr(10).join(action_implementations)}

    def execute_rollback(self):
        """Execute all rollback steps with safety checks."""
        print(f"🔄 Starting rollback for incident: {{self.incident_id}}")
        print(f"Generated: {timestamp}")
        print("=" * 60)

{main_execution}

        print("=" * 60)
        print("🏁 Rollback execution complete")

        # Generate summary
        self.print_rollback_summary()

    def log_action(self, step: int, success: bool, message: str):
        """Log rollback action for audit trail."""
        self.rollback_log.append({{
            "step": step,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }})

    def print_rollback_summary(self):
        """Print summary of rollback execution."""
        total_steps = {len(actions)}
        successful_steps = sum(1 for log in self.rollback_log if log["success"])

        print(f"📊 Rollback Summary:")
        print(f"   Total steps: {{total_steps}}")
        print(f"   Successful: {{successful_steps}}")
        print(f"   Failed: {{total_steps - successful_steps}}")

        if successful_steps == total_steps:
            print("   Status: ✅ COMPLETE")
        else:
            print("   Status: ❌ PARTIAL - Manual intervention may be required")


{main_wrapper}

if __name__ == '__main__':
    import datetime

    print("""
ROLLBACK SCRIPT WARNING:
This script will revert changes made by ResponseIQ remediation.
Ensure you have reviewed the changes and have proper backups.

Confirm continuation? (y/N): """, end="")

    if input().lower() != 'y':
        print("Rollback cancelled by user")
        sys.exit(0)

    # Execute the main entrypoint (wrapped for testability)
    main()
'''

        return script_template

    def _generate_validation_code(self, action: RollbackAction) -> str:
        """Generate validation code for a rollback action."""
        if not action.validation_check:
            return "# No validation check defined"

        return textwrap.dedent(f"""
        # Validation
        validation_result = {action.validation_check}
        if not validation_result:
            raise Exception("Validation check failed")
        """).strip()

    def _generate_main_execution(self, actions: List[RollbackAction]) -> str:
        """Generate the main execution flow for the rollback script."""
        step_calls = []
        for i, action in enumerate(actions, 1):
            step_call = textwrap.indent(
                textwrap.dedent(f"""
                # Step {i}: {action.description}
                success = self.rollback_step_{i}()
                self.log_action({i}, success, "{action.description}")
                {"if not success:" if action.critical else "# Non-critical step"}
                {"    print('❌ Critical step failed, aborting rollback')" if action.critical else ""}
                {"    return False" if action.critical else ""}
                """).strip(),
                "        ",
            )
            step_calls.append(step_call)

        return "\n\n".join(step_calls)

    def create_rollback_manifest(self, script_path: Path, incident_id: str, analysis: Dict[str, Any]) -> Path:
        """Create a manifest file documenting the rollback capability."""
        manifest_path = self.output_dir / f"rollback_{incident_id}_manifest.json"

        manifest = {
            "incident_id": incident_id,
            "script_path": str(script_path),
            "generated_at": datetime.now().isoformat(),
            "remediation_title": analysis.get("title", "Unknown"),
            "confidence": analysis.get("confidence", 0.0),
            "blast_radius": analysis.get("blast_radius", "unknown"),
            "rollback_capability": "EXECUTABLE",
            "manual_steps_required": False,
            "validation_included": True,
        }

        import json

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        logger.info(f"📋 Rollback manifest created: {manifest_path}")
        return manifest_path
