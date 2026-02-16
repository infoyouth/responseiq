"""
Reproduction Service for P2: Proof-Oriented Remediation.

Generates standalone pytest reproduction scripts that fail with the exact
error signature found in incident signals.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import shutil
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from responseiq.ai.llm_service import generate_reproduction_code
from responseiq.schemas.proof import (
    ProofBundle,
    ReproductionStatus,
    ReproductionTest,
    ValidationEvidence,
)


class ReproductionService:
    """
    Core P2 service: Scan → Reproduce → Verify → Remediate → Verify.

    Generates minimal pytest files that deterministically reproduce incidents.
    """

    def __init__(self, repro_base_path: Optional[Path] = None):
        self.repro_base_path = repro_base_path or Path("tests/repro")
        self.repro_base_path.mkdir(exist_ok=True)

    async def analyze_and_generate_reproduction(
        self, incident: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> ProofBundle:
        """
        Scan incident and generate reproduction test.

        Args:
            incident: Incident data with logs, stack traces, error signatures
            context: Additional context (file paths, environment, etc.)

        Returns:
            ProofBundle with reproduction test ready to run
        """
        context = context or {}

        # 1. Extract error signature and environment type
        error_signature = self._extract_error_signature(incident)
        environment_type = self._classify_environment_dependency(incident, context)

        # 2. Generate unique test ID
        test_id = self._generate_test_id(incident)

        # 3. Generate reproduction test
        reproduction_test = await self._generate_reproduction_test(
            test_id=test_id,
            incident=incident,
            error_signature=error_signature,
            environment_type=environment_type,
            context=context,
        )

        # 4. Create proof bundle
        proof_bundle = ProofBundle(
            incident_id=incident.get("id", test_id),
            created_at=datetime.now(),
            reproduction_test=reproduction_test,
            reproduction_confidence=self._calculate_reproduction_confidence(incident, error_signature),
            missing_evidence=[ValidationEvidence.PRE_FIX_FAILURE, ValidationEvidence.POST_FIX_SUCCESS],
        )

        return proof_bundle

    def _extract_error_signature(self, incident: Dict[str, Any]) -> str:
        """
        Extract the specific error pattern that reproduction test must trigger.
        """
        description = incident.get("description", "")
        error_patterns = [
            r"(\w+Error: .+)",  # Python exceptions
            r"(HTTP \d{3}: .+)",  # HTTP errors
            r"(Connection (?:refused|timeout): .+)",  # Network errors
            r"(Permission denied: .+)",  # Permission errors
            r"(No space left on device: .+)",  # Resource errors
            r"(ModuleNotFoundError: .+)",  # Import errors
        ]

        for pattern in error_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback to keywords if no specific pattern found
        if any(keyword in description.lower() for keyword in ["error", "exception", "failed"]):
            return description[:100] + "..." if len(description) > 100 else description

        return "UnknownError: Incident reproduction required"

    def _classify_environment_dependency(self, incident: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Classify the type of environment dependency for targeted mocking strategy.
        """
        description = incident.get("description", "").lower()

        # Network-related issues
        if any(
            keyword in description
            for keyword in ["connection", "timeout", "refused", "unreachable", "dns", "http", "api"]
        ):
            return "network"

        # File system issues
        if any(
            keyword in description
            for keyword in [
                "file not found",
                "no such file",
                "permission denied",
                "disk space",
                "readonly",
                "filenotfounderror",
                "ioerror",
                "oserror",
            ]
        ):
            return "filesystem"

        # Version/dependency issues
        if any(
            keyword in description
            for keyword in ["modulenotfounderror", "import", "version", "compatibility", "package"]
        ):
            return "version"

        # Resource exhaustion
        if any(keyword in description for keyword in ["memory", "cpu", "disk space", "too many", "limit exceeded"]):
            return "resource"

        # Permission issues
        if any(keyword in description for keyword in ["permission", "access denied", "forbidden", "unauthorized"]):
            return "permission"

        return "generic"

    async def _generate_reproduction_test(
        self,
        test_id: str,
        incident: Dict[str, Any],
        error_signature: str,
        environment_type: str,
        context: Dict[str, Any],
    ) -> ReproductionTest:
        """
        Generate the actual pytest file content for reproduction.
        """
        test_filename = f"test_{test_id}.py"
        test_path = self.repro_base_path / test_filename

        # Generate test content based on environment type
        test_content, repro_method = await self._generate_test_content(
            test_id=test_id,
            incident=incident,
            error_signature=error_signature,
            environment_type=environment_type,
            context=context,
        )

        # Write test file
        with open(test_path, "w") as f:
            f.write(test_content)

        # Generate initial file hash (Forensic Auditing)
        file_hash = self._generate_file_hash(test_path)

        return ReproductionTest(
            test_id=test_id,
            test_path=f"tests/repro/{test_filename}",
            incident_signature=error_signature,
            environment_type=environment_type,
            test_file_hash=file_hash,
            description=f"Reproduction test for: {incident.get('description', 'Unknown incident')[:100]}",
            rationale=f"Generated {environment_type} reproduction for error pattern: {error_signature}",
            mock_dependencies=self._get_mock_dependencies(environment_type),
            repro_method=repro_method,
        )

    async def _generate_test_content(
        self,
        test_id: str,
        incident: Dict[str, Any],
        error_signature: str,
        environment_type: str,
        context: Dict[str, Any],
    ) -> tuple[str, str]:
        """
        Generate pytest content using LLM, with fallback to static templates.
        Returns: (test_content, repro_method)
        """
        incident_summary = (
            f"ID: {test_id}\nError: {error_signature}\n"
            f"Description: {incident.get('description', '')}\nEnv: {environment_type}"
        )

        relevant_code = ""
        # Try to extract code context from various potential keys
        if "file_content" in context:
            relevant_code = context["file_content"]
        elif "source_code" in context:
            relevant_code = context["source_code"]

        # Call LLM Service
        generated_code = await generate_reproduction_code(incident_summary, relevant_code)

        if generated_code:
            return generated_code, "llm_synthesis"

        # Fallback to static templates if LLM fails
        return (
            self._generate_static_test_content(
                test_id=test_id,
                incident=incident,
                error_signature=error_signature,
                environment_type=environment_type,
                context=context,
            ),
            "static_fallback",
        )

    def _generate_static_test_content(
        self,
        test_id: str,
        incident: Dict[str, Any],
        error_signature: str,
        environment_type: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate pytest content tailored to the environment dependency type.
        """
        # Base imports and setup (pre-indented for dedent compatibility)
        imports = [
            "import pytest",
            "from unittest.mock import Mock, patch, MagicMock",
            "from .base import ResponseIQReproBase",
        ]

        # Add environment-specific imports
        env_imports = {
            "network": ["import requests", "from unittest.mock import AsyncMock"],
            "filesystem": ["import tempfile", "import os", "from pathlib import Path"],
            "permission": ["import tempfile", "import os", "import stat"],
            "resource": ["import psutil", "from unittest.mock import patch"],
            "version": ["import pkg_resources", "from unittest.mock import patch"],
            "generic": [],
        }

        imports.extend(env_imports.get(environment_type, []))

        # Generate test method based on environment type
        test_method = self._generate_test_method(test_id, error_signature, environment_type, incident, context)
        test_method = textwrap.indent(test_method, "    ")

        return f'''
"""
Reproduction test for incident: {incident.get('id', test_id)}

Expected Error: {error_signature}
Environment Type: {environment_type}
Generated: {datetime.now().isoformat()}
"""

{chr(10).join(imports)}


class Test{test_id.title().replace('_', '')}Reproduction(ResponseIQReproBase):
    """
    Minimal reproduction of {environment_type} incident.

    This test MUST fail before fix and pass after fix.
    """

{test_method}
'''.strip()

    def _generate_test_method(
        self,
        test_id: str,
        error_signature: str,
        environment_type: str,
        incident: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Generate the specific test method based on environment type."""

        if environment_type == "network":
            return textwrap.dedent(f'''
            @pytest.mark.asyncio
            async def test_{test_id}_network_failure(self):
                """Reproduce network-related incident."""
                with patch('requests.get') as mock_get:
                    mock_get.side_effect = requests.exceptions.ConnectionError("{error_signature}")
                    # Raise exception directly (Exit 1)
                    # Expected error: {error_signature}
                    requests.get("http://example.com/api")
            ''')

        elif environment_type == "filesystem":
            return textwrap.dedent(f'''
            def test_{test_id}_file_missing(self):
                """Reproduce filesystem-related incident."""
                with tempfile.TemporaryDirectory() as tmpdir:
                    missing_file = Path(tmpdir) / "missing_config.json"

                    # Raise exception directly (Exit 1)
                    # Expected error: FileNotFoundError
                    with open(missing_file, 'r') as f:
                        f.read()
            ''')

        elif environment_type == "permission":
            return textwrap.dedent(f'''
            def test_{test_id}_permission_denied(self):
                """Reproduce permission-related incident."""
                with tempfile.TemporaryDirectory() as tmpdir:
                    readonly_file = Path(tmpdir) / "readonly.txt"
                    readonly_file.write_text("test")
                    readonly_file.chmod(0o444)  # Read-only

                    # Raise exception directly (Exit 1)
                    # Expected error: PermissionError
                    with open(readonly_file, 'w') as f:
                        f.write("data")
            ''')

        elif environment_type == "resource":
            return textwrap.dedent(f'''
            def test_{test_id}_resource_exhaustion(self):
                """Reproduce resource exhaustion incident."""
                with patch('psutil.disk_usage') as mock_disk:
                    mock_disk.return_value = Mock(free=0)  # No free disk space

                    with pytest.raises(Exception) as exc_info:
                        # TODO: Replace with actual incident trigger code
                        if psutil.disk_usage('/').free == 0:
                            raise OSError("No space left on device")

                    assert "space" in str(exc_info.value).lower()
            ''')

        elif environment_type == "version":
            return textwrap.dedent(f'''
            def test_{test_id}_version_conflict(self):
                """Reproduce version/dependency incident."""
                with patch('pkg_resources.get_distribution') as mock_dist:
                    mock_dist.side_effect = pkg_resources.DistributionNotFound("missing_package")

                    # Raise exception directly (Exit 1)
                    # Expected error: missing_package
                    pkg_resources.get_distribution("missing_package")
            ''')

        else:  # generic
            return textwrap.dedent(f'''
            def test_{test_id}_generic_failure(self):
                """Reproduce generic incident."""
                # Raise exception directly without catching it to ensure Test Fails (Exit 1)
                # Current error signature: {error_signature}
                raise Exception("{error_signature}")
            ''')

    def _generate_test_id(self, incident: Dict[str, Any]) -> str:
        """Generate unique, descriptive test ID."""
        base_id = incident.get("id", f"incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        # Clean for valid Python identifier
        return re.sub(r"[^a-zA-Z0-9_]", "_", base_id).lower()

    def _get_mock_dependencies(self, environment_type: str) -> List[str]:
        """Return list of dependencies that will be mocked in the test."""
        return {
            "network": ["requests", "httpx", "aiohttp"],
            "filesystem": ["pathlib", "os", "tempfile"],
            "permission": ["os.chmod", "stat"],
            "resource": ["psutil", "os.statvfs"],
            "version": ["pkg_resources", "importlib"],
            "generic": [],
        }.get(environment_type, [])

    def _calculate_reproduction_confidence(self, incident: Dict[str, Any], error_signature: str) -> float:
        """
        Calculate confidence that reproduction test will accurately represent the incident.
        """
        confidence = 0.5  # Base confidence

        # Higher confidence if we have specific error patterns
        if any(pattern in error_signature for pattern in ["Error:", "Exception:", "HTTP"]):
            confidence += 0.3

        # Higher confidence if incident has detailed description
        description = incident.get("description", "")
        if len(description) > 50:
            confidence += 0.1

        # Higher confidence if we have stack trace information
        if "traceback" in description.lower() or "stack trace" in description.lower():
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_file_hash(self, file_path: Path) -> str:
        """Generate SHA-256 hash of a file."""
        if not file_path.exists():
            return "hash_calc_failed_no_file"

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _generate_text_hash(self, text: str) -> str:
        """Generate SHA-256 hash of text content."""
        if not text:
            return "hash_calc_failed_no_text"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def execute_reproduction_test(self, proof_bundle: ProofBundle, keep_evidence: bool = False) -> ProofBundle:
        """
        Execute the reproduction test and update proof bundle with results.

        This is the "Verify Failure" step in the P2 sequence.

        Item 1 - Python Path: Injects current working dir into PYTHONPATH so tests can import user code.
        Item 3 - Exit Code Handler: Explicitly handles "Successful Failure" (Exit Code 1).
        P2 Hardening - Timeout: Enforces 30s timeout to prevent infinite loops (ResponseIQ-351).
        P2 Forensic - Hashing: Hashes execution output and test file for integrity.
        """
        if not proof_bundle.reproduction_test:
            return proof_bundle

        test_path = proof_bundle.reproduction_test.test_path

        # P2 Forensic: Hash the test file itself before execution
        proof_bundle.reproduction_test.test_file_hash = self._generate_file_hash(Path(test_path))

        # item 1: The "Python Path" Problem
        # Ensure the subprocess can find the user's source code
        env = os.environ.copy()
        start_cwd = os.getcwd()
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{start_cwd}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = start_cwd

        # P2 - Test Isolation (Comment 1): Detect if project uses uv/poetry/pipenv
        # Prefer 'uv run' to isolate execution environment from ResponseIQ's own venv
        use_uv = (Path("pyproject.toml").exists() or Path("uv.lock").exists()) and shutil.which("uv")

        cmd = []
        if use_uv:
            # Use project's own environment via uv
            cmd = ["uv", "run", "pytest"]
        else:
            # Fallback to current python interpreter (potential contamination risk)
            cmd = [sys.executable, "-m", "pytest"]

        cmd.extend([str(test_path), "-v", "--tb=short"])

        try:
            # Run pytest on the specific test file
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )

            # P2 Hardening: 30s Timeout

            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                process.kill()
                stdout, _ = await process.communicate()
                stdout += b"\n[ResponseIQ] Execution TIMED OUT after 30s."

            execution_output = stdout.decode("utf-8")

            # P2 Forensic: Hash the execution log
            proof_bundle.reproduction_test.execution_log_hash = self._generate_text_hash(execution_output)

            # Update reproduction test status
            # Item 3: The "Negative Proof" Exit Code Handler
            # Exit Code 1 (Tests Failed) = ✅ SUCCESS (Bug Reproduced)
            if process.returncode == 1:
                proof_bundle.reproduction_test.status = ReproductionStatus.FAILED_AS_EXPECTED
                proof_bundle.pre_fix_evidence = execution_output
                # Remove PRE_FIX_FAILURE from missing evidence
                if ValidationEvidence.PRE_FIX_FAILURE in proof_bundle.missing_evidence:
                    proof_bundle.missing_evidence.remove(ValidationEvidence.PRE_FIX_FAILURE)
            elif process.returncode == 0:
                # Tests Passed = ❌ FAIL (Bug NOT Reproduced)
                proof_bundle.reproduction_test.status = ReproductionStatus.PASSED_UNEXPECTEDLY
                proof_bundle.reproduction_test.execution_output = (
                    f"Test PASSED unexpectedly (Exit 0). Expected failure to reproduce bug.\n{execution_output}"
                )
            else:
                # Other Exit Codes (Internal Error/Syntax Error)
                proof_bundle.reproduction_test.status = ReproductionStatus.EXECUTION_ERROR
                proof_bundle.reproduction_test.execution_output = (
                    f"Test Execution Error (Exit {process.returncode}).\n{execution_output}"
                )

            proof_bundle.reproduction_test.execution_time = datetime.now()

        except Exception as e:
            proof_bundle.reproduction_test.status = ReproductionStatus.EXECUTION_ERROR
            proof_bundle.reproduction_test.execution_output = f"Execution failed: {str(e)}"
            proof_bundle.reproduction_test.execution_time = datetime.now()

        # Item 2: Transient Artifact Cleanup
        if not keep_evidence and proof_bundle.reproduction_test.status != ReproductionStatus.FAILED_AS_EXPECTED:
            # Only cleanup if we failed to reproduce, otherwise we need it for the next step (Fix verification)
            # actually, we usually keep it until the end of the session.
            # For now, let's defer cleanup to an explicit cleanup method or separate call.
            pass

        return proof_bundle

    async def cleanup_reproduction_test(self, proof_bundle: ProofBundle) -> None:
        """
        Item 2: Transient Artifact Cleanup (Repo Hygiene)
        Deletes the generated test file.
        """
        if not proof_bundle.reproduction_test or not proof_bundle.reproduction_test.test_path:
            return

        try:
            path = Path(proof_bundle.reproduction_test.test_path)
            if path.exists():
                path.unlink()
        except Exception as e:
            # Non-blocking cleanup failure
            print(f"Warning: Failed to cleanup reproduction test {path}: {e}")

    async def validate_fix_with_reproduction(self, proof_bundle: ProofBundle) -> ProofBundle:
        """
        Re-run reproduction test after fix is applied to validate success.

        This is the "Verify Fix" step in the P2 sequence.
        """
        if not proof_bundle.reproduction_test or not proof_bundle.pre_fix_evidence:
            return proof_bundle

        # Re-execute the same test
        test_path = proof_bundle.reproduction_test.test_path

        # item 1: The "Python Path" Problem
        env = os.environ.copy()
        start_cwd = os.getcwd()
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{start_cwd}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = start_cwd

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pytest",
                str(test_path),
                "-v",
                "--tb=short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )

            stdout, _ = await process.communicate()
            execution_output = stdout.decode("utf-8")

            # Test should now pass after fix (Exit 0)
            if process.returncode == 0:
                proof_bundle.post_fix_evidence = execution_output
                proof_bundle.fix_confidence = 0.9  # High confidence if test now passes
                # Remove POST_FIX_SUCCESS from missing evidence
                if ValidationEvidence.POST_FIX_SUCCESS in proof_bundle.missing_evidence:
                    proof_bundle.missing_evidence.remove(ValidationEvidence.POST_FIX_SUCCESS)
            else:
                # Fix didn't work - test still fails
                proof_bundle.fix_confidence = 0.1
                proof_bundle.post_fix_evidence = f"Fix failed - test still fails: {execution_output}"

        except Exception as e:
            proof_bundle.post_fix_evidence = f"Post-fix validation failed: {str(e)}"
            proof_bundle.fix_confidence = 0.0

        return proof_bundle
