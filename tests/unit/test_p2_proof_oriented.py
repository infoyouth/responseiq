"""
P2 Proof-Oriented Remediation Tests

Tests the complete P2 workflow: Scan → Reproduce → Verify → Remediate → Verify
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from responseiq.schemas.proof import (
    ProofBundle,
    ReproductionStatus,
    ReproductionTest,
    ValidationEvidence,
)
from responseiq.services.remediation_service import RemediationService
from responseiq.services.reproduction_service import ReproductionService


class TestP2ProofOrientedRemediation:
    """
    Test P2 implementation: Proof-oriented remediation with reproduction tests.
    """

    @pytest.fixture
    def repro_service(self, tmp_path):
        """Return a reproduction service configured for testing."""
        return ReproductionService(repro_base_path=tmp_path / "repro")

    @pytest.fixture
    def high_impact_incident(self):
        """Return a mock incident with high enough impact to trigger P2 proof generation."""
        return {
            "id": "test-high-impact-001",
            "severity": "high",
            "description": "ConnectionError: Connection refused to API endpoint http://api.service.com/health",
            "source": "monitoring",
            "log_content": (
                "requests.exceptions.ConnectionError: "
                "HTTPSConnectionPool(host='api.service.com', port=443): Max retries exceeded"
            ),
        }

    @pytest.fixture
    def low_impact_incident(self):
        """Return a mock incident with low impact that should NOT trigger P2 proof generation."""
        return {
            "id": "test-low-impact-001",
            "severity": "low",
            "description": "Minor deprecation warning in log output",
            "source": "application",
        }

    @pytest.mark.asyncio
    async def test_analyze_and_generate_reproduction(self, repro_service, high_impact_incident):
        """Test P2 Step 1-2: Scan incident and generate reproduction test."""
        proof_bundle = await repro_service.analyze_and_generate_reproduction(high_impact_incident)

        # Verify proof bundle created
        assert proof_bundle is not None
        assert proof_bundle.incident_id == "test-high-impact-001"
        assert proof_bundle.reproduction_test is not None

        # Verify reproduction test metadata
        repro_test = proof_bundle.reproduction_test
        assert repro_test.environment_type == "network"
        assert "Connection refused" in repro_test.incident_signature
        assert repro_test.status == ReproductionStatus.NOT_RUN

        # Verify test file was created
        test_file = Path(repro_test.test_path)
        assert "test_" in test_file.name
        assert "network" in repro_test.environment_type

        # Verify missing evidence tracking
        assert ValidationEvidence.PRE_FIX_FAILURE in proof_bundle.missing_evidence
        assert ValidationEvidence.POST_FIX_SUCCESS in proof_bundle.missing_evidence

    @pytest.mark.asyncio
    async def test_execute_reproduction_test_success(self, repro_service, high_impact_incident, tmp_path):
        """Test P2 Step 3: Verify reproduction test fails as expected."""
        # Generate proof bundle with test file
        proof_bundle = await repro_service.analyze_and_generate_reproduction(high_impact_incident)

        # Mock pytest execution that fails (expected behavior)
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1  # Test failed as expected
            mock_process.communicate.return_value = (
                b"FAILED test_reproduction - ConnectionError: Connection refused",
                b"",
            )
            mock_subprocess.return_value = mock_process

            # Execute reproduction test
            updated_bundle = await repro_service.execute_reproduction_test(proof_bundle)

            # Verify test failed as expected (good!)
            assert updated_bundle.reproduction_test.status == ReproductionStatus.FAILED_AS_EXPECTED
            assert updated_bundle.pre_fix_evidence is not None
            assert "Connection refused" in updated_bundle.pre_fix_evidence
            assert ValidationEvidence.PRE_FIX_FAILURE not in updated_bundle.missing_evidence

    @pytest.mark.asyncio
    async def test_validate_fix_with_reproduction(self, repro_service, high_impact_incident):
        """Test P2 Step 5: Verify fix works by running reproduction test again."""
        # Setup proof bundle with pre-fix failure evidence
        proof_bundle = await repro_service.analyze_and_generate_reproduction(high_impact_incident)
        proof_bundle.pre_fix_evidence = "Test failed as expected before fix"

        # Mock pytest execution that now passes (fix worked!)
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0  # Test now passes after fix
            mock_process.communicate.return_value = (b"PASSED test_reproduction - fix successful", b"")
            mock_subprocess.return_value = mock_process

            # Validate fix
            updated_bundle = await repro_service.validate_fix_with_reproduction(proof_bundle)

            # Verify test now passes (fix worked!)
            assert updated_bundle.post_fix_evidence is not None
            assert "PASSED" in updated_bundle.post_fix_evidence
            assert updated_bundle.fix_confidence == 0.9
            assert ValidationEvidence.POST_FIX_SUCCESS not in updated_bundle.missing_evidence

    @pytest.mark.asyncio
    async def test_remediation_service_p2_integration(self, high_impact_incident):
        """Test P2 integration with RemediationService for high-impact incidents."""
        # Mock AI analysis to return high severity
        ai_analysis = {
            "title": "API Connection Failure",
            "remediation": "Check network connectivity and API endpoint health",
            "confidence": 0.8,
            "rationale": "Network connectivity issue identified from connection error logs",
        }

        with patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_llm:
            with patch.object(
                ReproductionService, "analyze_and_generate_reproduction", new_callable=AsyncMock
            ) as mock_repro:
                mock_llm.return_value = ai_analysis

                # Mock reproduction service to return proof bundle
                mock_proof_bundle = ProofBundle(
                    incident_id="test-high-impact-001",
                    created_at=datetime.now(),
                    reproduction_confidence=0.8,
                    missing_evidence=[ValidationEvidence.PRE_FIX_FAILURE],
                )
                mock_repro.return_value = mock_proof_bundle

                # Test remediation service
                remediation_service = RemediationService(environment="test")
                recommendation = await remediation_service.remediate_incident(high_impact_incident)

                # Verify P2 proof bundle was generated for high-impact incident
                assert recommendation.proof_bundle is not None
                assert recommendation.proof_bundle.incident_id == "test-high-impact-001"
                assert recommendation.impact_score >= 40.0  # High enough to trigger P2
                mock_repro.assert_called_once()

    @pytest.mark.asyncio
    async def test_low_impact_incident_skips_p2(self, low_impact_incident):
        """Test that low-impact incidents skip P2 proof generation."""
        ai_analysis = {
            "title": "Minor Warning",
            "remediation": "Update deprecated usage",
            "confidence": 0.6,
            "rationale": "Deprecation warning found in logs",
        }

        with patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock) as mock_llm:
            with patch(
                "responseiq.services.reproduction_service.ReproductionService.analyze_and_generate_reproduction"
            ) as mock_repro:
                mock_llm.return_value = ai_analysis

                # Test remediation service
                remediation_service = RemediationService(environment="test")
                recommendation = await remediation_service.remediate_incident(low_impact_incident)

                # Verify P2 proof generation was skipped for low-impact incident
                assert recommendation.proof_bundle is None
                assert recommendation.impact_score < 40.0  # Too low to trigger P2
                mock_repro.assert_not_called()

    def test_proof_bundle_blocks_guarded_apply(self):
        """Test that incomplete proof bundles block guarded_apply mode."""
        # Proof bundle with missing evidence
        incomplete_bundle = ProofBundle(
            incident_id="test-001",
            created_at=datetime.now(),
            missing_evidence=[ValidationEvidence.PRE_FIX_FAILURE, ValidationEvidence.POST_FIX_SUCCESS],
        )
        assert incomplete_bundle.blocks_guarded_apply is True
        assert incomplete_bundle.has_complete_proof is False

        # Complete proof bundle
        complete_bundle = ProofBundle(
            incident_id="test-001",
            created_at=datetime.now(),
            reproduction_test=ReproductionTest(
                test_id="test-001",
                test_path="tests/repro/test_001.py",
                incident_signature="ConnectionError",
                environment_type="network",
            ),
            pre_fix_evidence="Test failed before fix",
            post_fix_evidence="Test passed after fix",
            missing_evidence=[],  # No missing evidence
        )
        assert complete_bundle.blocks_guarded_apply is False
        assert complete_bundle.has_complete_proof is True

    def test_error_signature_extraction(self, repro_service):
        """Test extraction of error signatures from incident descriptions."""
        # Python exception
        incident = {"description": "Error occurred: ValueError: invalid input data provided"}
        signature = repro_service._extract_error_signature(incident)
        assert "ValueError: invalid input data provided" in signature

        # HTTP error
        incident = {"description": "HTTP 500: Internal server error on /api/users"}
        signature = repro_service._extract_error_signature(incident)
        assert "HTTP 500:" in signature

        # Connection error
        incident = {"description": "Connection timeout: unable to reach database after 30s"}
        signature = repro_service._extract_error_signature(incident)
        assert "Connection timeout:" in signature

    def test_environment_dependency_classification(self, repro_service):
        """Test classification of environment dependency types."""
        # Network incidents
        incident = {"description": "Connection refused to API endpoint"}
        env_type = repro_service._classify_environment_dependency(incident, {})
        assert env_type == "network"

        # Filesystem incidents
        incident = {"description": "FileNotFoundError: config.json not found"}
        env_type = repro_service._classify_environment_dependency(incident, {})
        assert env_type == "filesystem"

        # Permission incidents
        incident = {"description": "PermissionError: access denied to /var/log"}
        env_type = repro_service._classify_environment_dependency(incident, {})
        assert env_type == "permission"

        # Version/dependency incidents
        incident = {"description": "ModuleNotFoundError: No module named 'missing_pkg'"}
        env_type = repro_service._classify_environment_dependency(incident, {})
        assert env_type == "version"

        # Generic fallback
        incident = {"description": "Something went wrong"}
        env_type = repro_service._classify_environment_dependency(incident, {})
        assert env_type == "generic"
