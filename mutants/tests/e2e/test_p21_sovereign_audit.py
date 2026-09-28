"""
End-to-end tests for P2.1 "Sovereign Audit" Release features.
Tests Shadow Analytics, Forensic Integrity, and Executable Rollbacks.
"""

import hashlib
import json
from datetime import datetime, timedelta

import pytest

from responseiq.schemas.incident import Incident, IncidentSeverity, LogEntry
from responseiq.schemas.proof import Evidence, EvidenceIntegrity
from responseiq.services.rollback_generator import ExecutableRollbackGenerator
from responseiq.services.shadow_analytics import ShadowAnalyticsService


class TestP21SovereignAudit:
    """E2E tests for P2.1 Sovereign Audit features."""

    @pytest.fixture
    def shadow_service(self):
        return ShadowAnalyticsService()

    @pytest.fixture
    def rollback_generator(self):
        return ExecutableRollbackGenerator()

    @pytest.fixture
    def sample_incident(self):
        return Incident(
            id="TEST-001",
            title="Database Connection Pool Exhaustion",
            description="PostgreSQL connection pool exhausted causing 500 errors",
            severity=IncidentSeverity.HIGH,
            service="web-api",
            logs=[
                LogEntry(
                    timestamp=datetime.now(),
                    level="ERROR",
                    service="web-api",
                    message="django.db.utils.OperationalError: connection pool exhausted",
                )
            ],
            tags=["database", "postgresql", "production"],
            created_at=datetime.now(),
            resolved_at=None,
            source_repo="https://github.com/test/repo",
        )

    @pytest.fixture
    def sample_evidence(self):
        return Evidence(
            type="shadow_analysis",
            content={"test": "data", "timestamp": datetime.now().isoformat()},
            source="responseiq_shadow_analytics",
            timestamp=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_shadow_analytics_incident_analysis(self, shadow_service, sample_incident):
        """Test shadow analysis of individual incident."""
        result = await shadow_service.analyze_incident_shadow(sample_incident)

        # Verify result structure
        assert result.incident_id == sample_incident.id
        assert result.shadow_mode is True
        assert 0 <= result.confidence_score <= 1
        assert result.projected_fix_time_minutes > 0
        assert 1 <= result.value_score <= 10
        assert result.risk_assessment in ["LOW", "MEDIUM", "HIGH"]
        assert len(result.reasoning) > 0
        assert result.automation_candidate is not None

    @pytest.mark.asyncio
    async def test_shadow_analytics_period_report(self, shadow_service):
        """Test period report generation for management."""
        # Generate report for last 7 days
        report = await shadow_service.generate_period_report(
            start_date=datetime.now() - timedelta(days=7), end_date=datetime.now()
        )

        # Verify report structure
        assert report.period_days == 7
        assert report.total_incidents >= 0
        assert report.automation_candidates >= 0
        assert report.projected_annual_savings >= 0
        assert report.avg_time_saved_minutes >= 0
        assert report.roi_projection >= 0
        assert len(report.executive_summary) > 0
        assert "ResponseIQ" in report.executive_summary

    def test_forensic_integrity_evidence_sealing(self, sample_evidence):
        """Test evidence sealing with cryptographic hashing."""
        integrity = EvidenceIntegrity()

        # Seal evidence
        sealed = integrity.seal_evidence(sample_evidence)

        # Verify sealing
        assert sealed.integrity_hash is not None
        assert len(sealed.integrity_hash) == 64  # SHA-256 hex length
        assert sealed.chain_hash is not None
        assert sealed.sealed_at is not None
        assert sealed.algorithm == "SHA-256"

    def test_forensic_integrity_verification(self, sample_evidence):
        """Test evidence integrity verification."""
        integrity = EvidenceIntegrity()

        # Seal original evidence
        sealed = integrity.seal_evidence(sample_evidence)

        # Verify original is valid
        assert integrity.verify_evidence_integrity(sealed, sample_evidence) is True

        # Create tampered evidence
        tampered_evidence = Evidence(
            type=sample_evidence.type,
            content={"tampered": "data"},  # Different content
            source=sample_evidence.source,
            timestamp=sample_evidence.timestamp,
        )

        # Verify tampering detection
        assert integrity.verify_evidence_integrity(sealed, tampered_evidence) is False

    def test_forensic_integrity_chain_verification(self, sample_evidence):
        """Test evidence chain verification."""
        integrity = EvidenceIntegrity()

        # Create evidence chain
        evidence1 = sample_evidence
        sealed1 = integrity.seal_evidence(evidence1)

        evidence2 = Evidence(type="follow_up", content={"follow_up": "data"}, source="test", timestamp=datetime.now())
        sealed2 = integrity.seal_evidence(evidence2, previous_hash=sealed1.integrity_hash)

        # Verify chain
        assert sealed2.chain_hash is not None
        assert sealed2.chain_hash != sealed1.integrity_hash

        # Test chain verification (this would be more complex in real implementation)
        expected_chain_hash = hashlib.sha256(f"{sealed2.integrity_hash}{sealed1.integrity_hash}".encode()).hexdigest()
        assert sealed2.chain_hash == expected_chain_hash

    @pytest.mark.asyncio
    async def test_executable_rollback_generation(self, rollback_generator):
        """Test generation of executable rollback scripts."""
        changes = ["ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"]
        context = {"database": "postgresql", "table": "users"}

        script = await rollback_generator.generate_rollback_script(changes, context)

        # Verify script content
        assert len(script) > 0
        assert "#!/usr/bin/env python3" in script
        assert "rollback" in script.lower()
        assert "def main()" in script
        assert "if __name__ == '__main__'" in script

        # Verify safety features
        assert "dry_run" in script.lower() or "confirm" in script.lower()
        assert "backup" in script.lower() or "snapshot" in script.lower()

    @pytest.mark.asyncio
    async def test_executable_rollback_validation(self, rollback_generator):
        """Test rollback script validation."""
        changes = ["kubectl set image deployment/web-api web-api=web-api:v2.1.3"]
        context = {"namespace": "production", "deployment": "web-api"}

        script = await rollback_generator.generate_rollback_script(changes, context)

        # Validate script syntax by attempting to compile
        try:
            compile(script, "<rollback_script>", "exec")
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False

        assert syntax_valid, "Generated rollback script has syntax errors"

    @pytest.mark.asyncio
    async def test_executable_rollback_different_contexts(self, rollback_generator):
        """Test rollback generation for different system contexts."""
        test_cases = [
            {
                "name": "Database Rollback",
                "changes": ["ALTER TABLE orders ADD COLUMN status VARCHAR(20)"],
                "context": {"database": "postgresql", "table": "orders"},
            },
            {
                "name": "Kubernetes Rollback",
                "changes": ["kubectl scale deployment payment-service --replicas=5"],
                "context": {"namespace": "prod", "deployment": "payment-service"},
            },
            {
                "name": "Environment Variable Rollback",
                "changes": ["export REDIS_MAX_MEMORY=8192MB"],
                "context": {"service": "cache", "env_var": "REDIS_MAX_MEMORY"},
            },
        ]

        for case in test_cases:
            script = await rollback_generator.generate_rollback_script(case["changes"], case["context"])

            # Basic validation
            assert len(script) > 100, f"{case['name']} script too short"
            assert "def main()" in script, f"{case['name']} missing main function"
            assert "rollback" in script.lower(), f"{case['name']} missing rollback logic"

    @pytest.mark.asyncio
    async def test_p21_integration_workflow(self, shadow_service, rollback_generator, sample_incident):
        """Test complete P2.1 workflow integration."""
        # Step 1: Shadow Analysis
        shadow_result = await shadow_service.analyze_incident_shadow(sample_incident)
        assert shadow_result.shadow_mode is True
        assert shadow_result.confidence_score > 0

        # Step 2: Forensic Evidence
        evidence = Evidence(
            type="shadow_analysis", content=shadow_result.dict(), source="responseiq_shadow", timestamp=datetime.now()
        )

        integrity = EvidenceIntegrity()
        sealed_evidence = integrity.seal_evidence(evidence)
        assert integrity.verify_evidence_integrity(sealed_evidence, evidence)

        # Step 3: Executable Rollback
        changes = ["git revert abc123"]
        context = {"repo": sample_incident.source_repo, "commit": "abc123"}

        rollback_script = await rollback_generator.generate_rollback_script(changes, context)
        assert "git revert" in rollback_script

        # Verify complete workflow
        assert shadow_result is not None
        assert sealed_evidence.integrity_hash is not None
        assert len(rollback_script) > 0

    @pytest.mark.asyncio
    async def test_p21_cli_shadow_mode_compatibility(self, shadow_service, sample_incident):
        """Test CLI compatibility with P2.1 shadow mode."""
        # Simulate CLI shadow analysis
        result = await shadow_service.analyze_incident_shadow(sample_incident)

        # Test JSON serialization (for CLI output)
        json_output = json.dumps(result.dict(), default=str)
        parsed = json.loads(json_output)

        assert parsed["incident_id"] == sample_incident.id
        assert parsed["shadow_mode"] is True
        assert "confidence_score" in parsed

        # Test period report serialization
        report = await shadow_service.generate_period_report(datetime.now() - timedelta(days=1), datetime.now())

        report_json = json.dumps(report.dict(), default=str)
        report_parsed = json.loads(report_json)

        assert "total_incidents" in report_parsed
        assert "projected_annual_savings" in report_parsed

    def test_p21_compliance_metrics(self, sample_evidence):
        """Test P2.1 compliance with enterprise audit requirements."""
        integrity = EvidenceIntegrity()
        sealed = integrity.seal_evidence(sample_evidence)

        # Audit trail requirements
        assert sealed.sealed_at is not None  # Timestamp
        assert sealed.integrity_hash is not None  # Cryptographic proof
        assert sealed.algorithm == "SHA-256"  # Industry standard
        assert len(sealed.integrity_hash) == 64  # Full hash length

        # Non-repudiation
        is_valid = integrity.verify_evidence_integrity(sealed, sample_evidence)
        assert is_valid  # Verifiable integrity

        # Tamper detection
        fake_evidence = Evidence(type="fake", content={"fake": "data"}, source="fake", timestamp=datetime.now())
        is_fake_valid = integrity.verify_evidence_integrity(sealed, fake_evidence)
        assert not is_fake_valid  # Detects tampering

    def test_p21_performance_requirements(self):
        """Test P2.1 performance meets enterprise requirements."""
        # Test evidence sealing performance
        integrity = EvidenceIntegrity()

        start_time = datetime.now()

        # Create and seal 100 evidence items
        for i in range(100):
            evidence = Evidence(
                type="performance_test",
                content={"test_id": i, "data": f"test_data_{i}"},
                source="performance_test",
                timestamp=datetime.now(),
            )
            sealed = integrity.seal_evidence(evidence)
            assert sealed.integrity_hash is not None

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should process 100 evidence items in under 5 seconds
        assert duration < 5.0, f"Evidence sealing took {duration}s, should be < 5s"

    @pytest.mark.asyncio
    async def test_p21_error_handling(self, shadow_service, rollback_generator):
        """Test P2.1 error handling and resilience."""
        # Test shadow analysis with malformed incident
        malformed_incident = Incident(
            id="",  # Invalid empty ID
            title="Test",
            description="Test",
            severity=IncidentSeverity.LOW,
            service="test",
            logs=[],
            tags=[],
            created_at=datetime.now(),
            resolved_at=None,
            source_repo="",
        )

        # Should handle gracefully
        result = await shadow_service.analyze_incident_shadow(malformed_incident)
        assert result is not None  # Should not crash

        # Test rollback with empty changes
        script = await rollback_generator.generate_rollback_script([], {})
        assert len(script) > 0  # Should generate basic script even with no changes

    def test_p21_security_requirements(self, sample_evidence):
        """Test P2.1 security and data protection requirements."""
        integrity = EvidenceIntegrity()

        # Test hash collision resistance (basic check)
        evidence1 = sample_evidence
        evidence2 = Evidence(
            type=sample_evidence.type,
            content={"different": "content"},
            source=sample_evidence.source,
            timestamp=sample_evidence.timestamp,
        )

        sealed1 = integrity.seal_evidence(evidence1)
        sealed2 = integrity.seal_evidence(evidence2)

        # Different evidence should have different hashes
        assert sealed1.integrity_hash != sealed2.integrity_hash

        # Hash should be deterministic
        sealed1_again = integrity.seal_evidence(evidence1)
        assert sealed1.integrity_hash == sealed1_again.integrity_hash
