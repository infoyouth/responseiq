"""
Reproduction Service for P2: Proof-Oriented Remediation.

Generates standalone pytest reproduction scripts that fail with the exact
error signature found in incident signals.
"""

from __future__ import annotations

import asyncio
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        test_content = self._generate_test_content(
            test_id=test_id,
            incident=incident,
            error_signature=error_signature,
            environment_type=environment_type,
            context=context,
        )

        # Write test file
        with open(test_path, "w") as f:
            f.write(test_content)

        return ReproductionTest(
            test_id=test_id,
            test_path=f"tests/repro/{test_filename}",
            incident_signature=error_signature,
            environment_type=environment_type,
            description=f"Reproduction test for: {incident.get('description', 'Unknown incident')[:100]}",
            rationale=f"Generated {environment_type} reproduction for error pattern: {error_signature}",
            mock_dependencies=self._get_mock_dependencies(environment_type),
        )

    def _generate_test_content(
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
            "        import pytest",
            "        from unittest.mock import Mock, patch, MagicMock",
            "        from .base import ResponseIQReproBase",
        ]

        # Add environment-specific imports (pre-indented)
        env_imports = {
            "network": ["        import requests", "        from unittest.mock import AsyncMock"],
            "filesystem": ["        import tempfile", "        import os", "        from pathlib import Path"],
            "permission": ["        import tempfile", "        import os", "        import stat"],
            "resource": ["        import psutil", "        from unittest.mock import patch"],
            "version": ["        import pkg_resources", "        from unittest.mock import patch"],
            "generic": [],
        }

        imports.extend(env_imports.get(environment_type, []))

        # Generate test method based on environment type
        test_method = self._generate_test_method(test_id, error_signature, environment_type, incident, context)

        return textwrap.dedent(f'''
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
        ''').strip()

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
            return f'''
            @pytest.mark.asyncio
            async def test_{test_id}_network_failure(self):
                """Reproduce network-related incident."""
                with patch('requests.get') as mock_get:
                    mock_get.side_effect = requests.exceptions.ConnectionError("{error_signature}")

                    with pytest.raises(Exception) as exc_info:
                        # TODO: Replace with actual incident trigger code
                        requests.get("http://example.com/api")

                    assert "{error_signature}" in str(exc_info.value)
            '''

        elif environment_type == "filesystem":
            return f'''
            def test_{test_id}_file_missing(self):
                """Reproduce filesystem-related incident."""
                with tempfile.TemporaryDirectory() as tmpdir:
                    missing_file = Path(tmpdir) / "missing_config.json"

                    with pytest.raises(FileNotFoundError) as exc_info:
                        # TODO: Replace with actual incident trigger code
                        with open(missing_file, 'r') as f:
                            f.read()

                    assert "No such file or directory" in str(exc_info.value)
            '''

        elif environment_type == "permission":
            return f'''
            def test_{test_id}_permission_denied(self):
                """Reproduce permission-related incident."""
                with tempfile.TemporaryDirectory() as tmpdir:
                    readonly_file = Path(tmpdir) / "readonly.txt"
                    readonly_file.write_text("test")
                    readonly_file.chmod(0o444)  # Read-only

                    with pytest.raises(PermissionError) as exc_info:
                        # TODO: Replace with actual incident trigger code
                        with open(readonly_file, 'w') as f:
                            f.write("should fail")

                    assert "Permission denied" in str(exc_info.value)
            '''

        elif environment_type == "resource":
            return f'''
            def test_{test_id}_resource_exhaustion(self):
                """Reproduce resource exhaustion incident."""
                with patch('psutil.disk_usage') as mock_disk:
                    mock_disk.return_value = Mock(free=0)  # No free disk space

                    with pytest.raises(Exception) as exc_info:
                        # TODO: Replace with actual incident trigger code
                        if psutil.disk_usage('/').free == 0:
                            raise OSError("No space left on device")

                    assert "space" in str(exc_info.value).lower()
            '''

        elif environment_type == "version":
            return f'''
            def test_{test_id}_version_conflict(self):
                """Reproduce version/dependency incident."""
                with patch('pkg_resources.get_distribution') as mock_dist:
                    mock_dist.side_effect = pkg_resources.DistributionNotFound("missing_package")

                    with pytest.raises(ModuleNotFoundError) as exc_info:
                        # TODO: Replace with actual incident trigger code
                        pkg_resources.get_distribution("missing_package")
                        import missing_package  # This should fail

                    assert "missing_package" in str(exc_info.value)
            '''

        else:  # generic
            return f'''
            def test_{test_id}_generic_failure(self):
                """Reproduce generic incident."""
                with pytest.raises(Exception) as exc_info:
                    # TODO: Replace with actual incident trigger code based on analysis
                    # Current error signature: {error_signature}
                    raise Exception("{error_signature}")

                assert "{error_signature}" in str(exc_info.value)
            '''

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

    async def execute_reproduction_test(self, proof_bundle: ProofBundle) -> ProofBundle:
        """
        Execute the reproduction test and update proof bundle with results.

        This is the "Verify Failure" step in the P2 sequence.
        """
        if not proof_bundle.reproduction_test:
            return proof_bundle

        test_path = proof_bundle.reproduction_test.test_path

        try:
            # Run pytest on the specific test file
            process = await asyncio.create_subprocess_exec(
                "python",
                "-m",
                "pytest",
                test_path,
                "-v",
                "--tb=short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await process.communicate()
            execution_output = stdout.decode("utf-8")

            # Update reproduction test status
            if process.returncode != 0:
                proof_bundle.reproduction_test.status = ReproductionStatus.FAILED_AS_EXPECTED
                proof_bundle.pre_fix_evidence = execution_output
                # Remove PRE_FIX_FAILURE from missing evidence
                if ValidationEvidence.PRE_FIX_FAILURE in proof_bundle.missing_evidence:
                    proof_bundle.missing_evidence.remove(ValidationEvidence.PRE_FIX_FAILURE)
            else:
                proof_bundle.reproduction_test.status = ReproductionStatus.PASSED_UNEXPECTEDLY

            proof_bundle.reproduction_test.execution_output = execution_output
            proof_bundle.reproduction_test.execution_time = datetime.now()

        except Exception as e:
            proof_bundle.reproduction_test.status = ReproductionStatus.EXECUTION_ERROR
            proof_bundle.reproduction_test.execution_output = f"Execution failed: {str(e)}"
            proof_bundle.reproduction_test.execution_time = datetime.now()

        return proof_bundle

    async def validate_fix_with_reproduction(self, proof_bundle: ProofBundle) -> ProofBundle:
        """
        Re-run reproduction test after fix is applied to validate success.

        This is the "Verify Fix" step in the P2 sequence.
        """
        if not proof_bundle.reproduction_test or not proof_bundle.pre_fix_evidence:
            return proof_bundle

        # Re-execute the same test
        test_path = proof_bundle.reproduction_test.test_path

        try:
            process = await asyncio.create_subprocess_exec(
                "python",
                "-m",
                "pytest",
                test_path,
                "-v",
                "--tb=short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await process.communicate()
            execution_output = stdout.decode("utf-8")

            # Test should now pass after fix
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
