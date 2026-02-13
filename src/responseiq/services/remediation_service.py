"""
Remediation Service with Trust Gate Integration
Enterprise-ready remediation with policy enforcement, safety checks, and structured outputs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from responseiq.ai.llm_service import analyze_with_llm
from responseiq.config.policy_config import PolicyMode
from responseiq.schemas.proof import ProofBundle
from responseiq.services.impact import assess_impact
from responseiq.services.reproduction_service import ReproductionService
from responseiq.services.rollback_generator import ExecutableRollbackGenerator
from responseiq.services.trust_gate import (
    RemediationRequest,
    TrustGateValidator,
    ValidationResult,
)
from responseiq.utils.k8s_patcher import KubernetesPatcher
from responseiq.utils.logger import logger


@dataclass
class RemediationRecommendation:
    """Structured remediation output with trust and safety metadata."""

    incident_id: str
    title: str
    severity: str
    confidence: float
    impact_score: float
    blast_radius: str

    # Core remediation content
    rationale: str
    remediation_plan: str
    affected_files: List[str] = field(default_factory=list)
    proposed_changes: List[Dict[str, Any]] = field(default_factory=list)

    # Trust gate results
    allowed: bool = False
    policy_validation: Optional[ValidationResult] = None
    execution_mode: Optional[PolicyMode] = None

    # Safety and reversibility
    rollback_plan: Optional[str] = None
    test_plan: Optional[str] = None
    risk_assessment: Dict[str, Any] = field(default_factory=dict)

    # Evidence and proof
    evidence: Dict[str, Any] = field(default_factory=dict)
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    proof_bundle: Optional[ProofBundle] = None  # P2: Proof-oriented evidence

    # Execution guidance
    required_actions: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "severity": self.severity,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "blast_radius": self.blast_radius,
            "rationale": self.rationale,
            "remediation_plan": self.remediation_plan,
            "affected_files": self.affected_files,
            "proposed_changes": self.proposed_changes,
            "allowed": self.allowed,
            "execution_mode": self.execution_mode.value if self.execution_mode else None,
            "rollback_plan": self.rollback_plan,
            "test_plan": self.test_plan,
            "risk_assessment": self.risk_assessment,
            "evidence": self.evidence,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "required_actions": self.required_actions,
            "next_steps": self.next_steps,
        }


class RemediationService:
    """
    Enterprise-grade remediation service with Trust Gate integration.
    Provides safe, policy-governed, explainable incident remediation.
    """

    def __init__(self, environment: str = "production"):
        self.k8s_patcher = KubernetesPatcher()
        self.trust_gate = TrustGateValidator(environment=environment)
        self.reproduction_service = ReproductionService()  # P2: Proof-oriented testing
        self.rollback_generator = ExecutableRollbackGenerator()  # P2.1: Executable rollbacks
        self.environment = environment

        logger.info(f"RemediationService initialized for {environment} environment")
        logger.info(f"Policy summary: {self.trust_gate.get_policy_summary()}")

    async def remediate_incident(
        self, incident: dict, context_path: Optional[Path] = None
    ) -> RemediationRecommendation:
        """
        Main entry point for incident remediation with full trust gate validation.

        Returns structured remediation recommendation with safety metadata.
        """
        # Generate unique incident ID if not provided
        incident_id = incident.get("id", str(uuid.uuid4()))

        logger.info(f"Starting trust-gate remediation for incident: {incident_id}")

        # Step 1: Extract and analyze incident data
        log_content = incident.get("log_content") or incident.get("reason") or "No log provided"
        severity = incident.get("severity", "medium").lower()

        # Step 2: AI analysis for remediation plan
        analysis_result = await analyze_with_llm(log_content)

        if not analysis_result:
            return self._create_failed_recommendation(
                incident_id, "AI analysis failed or was skipped (API Key missing?)"
            )

        title = analysis_result.get("title", "Unknown Issue")
        remediation_plan = analysis_result.get("remediation")
        ai_confidence = analysis_result.get("confidence", 0.6)

        if not remediation_plan:
            return self._create_failed_recommendation(
                incident_id, f"AI analyzed '{title}' but provided no specific remediation steps."
            )

        logger.info(f"AI analysis complete for '{title}' with confidence: {ai_confidence}")

        # Step 3: Assess incident impact
        impact_assessment = assess_impact(
            severity=severity, title=title, description=log_content, source="ai", confidence=ai_confidence
        )

        # Step 3.5: Generate proof bundle for high-impact incidents (P2)
        proof_bundle = None
        if impact_assessment.score >= 40.0:
            logger.info(f"High-impact incident ({impact_assessment.score:.1f} ≥ 40): Generating reproduction test")
            try:
                proof_bundle = await self.reproduction_service.analyze_and_generate_reproduction(
                    incident=incident, context={"impact_assessment": impact_assessment, "ai_analysis": analysis_result}
                )
                if proof_bundle.reproduction_test:
                    logger.info(f"✅ Reproduction test generated: {proof_bundle.reproduction_test.test_path}")
                else:
                    logger.warning("⚠️  Reproduction test generation completed but no test was created")
            except Exception as e:
                logger.warning(f"⚠️  Failed to generate reproduction test: {str(e)}")

        # Step 4: Build remediation request for trust gate
        blast_radius = impact_assessment.factors.get("affected_surface", "single_service")

        # Extract affected files and changes from AI analysis
        affected_files = analysis_result.get("affected_files", [])
        proposed_changes = analysis_result.get("proposed_changes", [])

        # Generate rollback and test plans
        rollback_plan = await self._generate_rollback_plan(analysis_result, affected_files, proposed_changes)
        test_plan = self._generate_test_plan(analysis_result, title)

        remediation_request = RemediationRequest(
            incident_id=incident_id,
            severity=severity,
            confidence=ai_confidence,
            impact_score=impact_assessment.score,
            blast_radius=blast_radius,
            affected_files=affected_files,
            proposed_changes=proposed_changes,
            rollback_plan=rollback_plan,
            test_plan=test_plan,
            rationale=analysis_result.get("rationale", "AI-generated remediation based on incident analysis"),
        )

        # Step 5: Trust gate validation
        validation_result = await self.trust_gate.validate_remediation(remediation_request)

        # Step 6: Build comprehensive recommendation
        recommendation = RemediationRecommendation(
            incident_id=incident_id,
            title=title,
            severity=severity,
            confidence=ai_confidence,
            impact_score=impact_assessment.score,
            blast_radius=blast_radius,
            rationale=remediation_request.rationale or "AI-generated remediation based on incident analysis",
            remediation_plan=remediation_plan,
            affected_files=affected_files,
            proposed_changes=proposed_changes,
            allowed=validation_result.allowed,
            policy_validation=validation_result,
            execution_mode=validation_result.policy_mode,
            rollback_plan=rollback_plan,
            test_plan=test_plan,
            evidence=validation_result.evidence,
            checks_passed=validation_result.checks_passed,
            checks_failed=validation_result.checks_failed,
            required_actions=validation_result.required_actions,
            proof_bundle=proof_bundle,  # P2: Proof-oriented evidence
        )

        # Step 7: Add risk assessment
        recommendation.risk_assessment = self._assess_remediation_risk(
            validation_result, impact_assessment, analysis_result
        )

        # Step 8: Generate next steps based on validation result
        recommendation.next_steps = self._generate_next_steps(validation_result, recommendation)

        # Log final decision
        if validation_result.allowed:
            logger.info(f"✅ Remediation APPROVED for {incident_id}: {validation_result.message}")
        else:
            logger.warning(f"❌ Remediation DENIED for {incident_id}: {validation_result.message}")

        return recommendation

    def _create_failed_recommendation(self, incident_id: str, reason: str) -> RemediationRecommendation:
        """Create a failed remediation recommendation."""
        return RemediationRecommendation(
            incident_id=incident_id,
            title="Remediation Failed",
            severity="unknown",
            confidence=0.0,
            impact_score=0.0,
            blast_radius="unknown",
            rationale=reason,
            remediation_plan="No remediation available",
            allowed=False,
            required_actions=["Review incident data and retry analysis"],
            next_steps=["Check AI service availability", "Verify incident data quality"],
        )

    async def _generate_rollback_plan(
        self, analysis_result: dict, affected_files: List[str], proposed_changes: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate executable rollback script and return reference."""
        if not affected_files:
            return "No file changes detected - no rollback required"

        # Generate incident ID for the rollback script
        incident_id = analysis_result.get("incident_id", f"auto_{uuid.uuid4().hex[:8]}")

        # Use the executable rollback generator
        try:
            # Await the (now async) generator. It still supports the file-backed
            # keyword-argument style and will return a Path for that usage.
            script_path = await self.rollback_generator.generate_rollback_script(
                incident_id=incident_id,
                analysis_result=analysis_result,
                affected_files=affected_files,
                proposed_changes=proposed_changes or [],
            )

            # Create manifest for audit trail
            manifest_path = self.rollback_generator.create_rollback_manifest(script_path, incident_id, analysis_result)

            return f"Executable rollback script: {script_path}\nManifest: {manifest_path}"

        except Exception as e:
            logger.warning(f"Failed to generate executable rollback script: {e}")
            # Fallback to text-based plan
            return self._generate_text_rollback_plan(analysis_result, affected_files)

    def _generate_text_rollback_plan(self, analysis_result: dict, affected_files: List[str]) -> str:
        """Fallback text-based rollback plan."""
        rollback_steps = [
            "# Rollback Plan (Text-based fallback)",
            f"# Generated for incident analysis: {analysis_result.get('title', 'Unknown')}",
            "",
            "1. Create backup of current state:",
            "   git stash push -m 'Pre-remediation backup'",
            "",
            "2. Revert to previous working state:",
            "   git reset --hard HEAD~1",
            "",
            "3. Verify system health:",
            "   kubectl get pods --all-namespaces",
            "   curl -f http://healthcheck-endpoint/health",
            "",
            "4. If issues persist, contact on-call engineer",
            "",
            f"# Affected files: {', '.join(affected_files)}",
        ]

        return "\n".join(rollback_steps)

    def _generate_test_plan(self, analysis_result: dict, title: str) -> str:
        """Generate validation test plan."""
        test_steps = [
            "# Test Plan",
            f"# Validation for: {title}",
            "",
            "1. Pre-remediation validation:",
            "   - Reproduce the original issue",
            "   - Document current error state",
            "",
            "2. Post-remediation validation:",
            "   - Verify error no longer occurs",
            "   - Run smoke tests on affected services",
            "   - Monitor metrics for 15 minutes",
            "",
            "3. Acceptance criteria:",
            "   - ✅ Original error resolved",
            "   - ✅ No new errors introduced",
            "   - ✅ Service performance within normal range",
            "",
            "4. Monitoring checklist:",
            "   - [ ] Error rate < baseline",
            "   - [ ] Response time < 95th percentile",
            "   - [ ] No alert escalations",
        ]

        return "\n".join(test_steps)

    def _assess_remediation_risk(self, validation: ValidationResult, impact: Any, analysis: dict) -> Dict[str, Any]:
        """Assess overall risk of remediation."""
        risk_factors = {
            "validation_passed": validation.allowed,
            "confidence_level": (
                "high" if validation.confidence_used > 0.8 else "medium" if validation.confidence_used > 0.6 else "low"
            ),
            "impact_score": impact.score,
            "blast_radius": validation.evidence.get("blast_radius", "unknown"),
            "protected_paths": len(
                [f for f in analysis.get("affected_files", []) if "/production/" in f or "/etc/" in f]
            ),
            "checks_passed": len(validation.checks_passed),
            "checks_failed": len(validation.checks_failed),
        }

        # Calculate overall risk score (0-100, lower is safer)
        risk_score = 0
        if not validation.allowed:
            risk_score += 50
        if validation.confidence_used < 0.7:
            risk_score += 20
        if impact.score < 40:
            risk_score += 15
        if validation.checks_failed:
            risk_score += len(validation.checks_failed) * 10

        risk_factors["overall_risk_score"] = min(100, risk_score)
        risk_factors["overall_risk_level"] = "high" if risk_score > 60 else "medium" if risk_score > 30 else "low"

        return risk_factors

    def _generate_next_steps(
        self, validation: ValidationResult, recommendation: RemediationRecommendation
    ) -> List[str]:
        """Generate actionable next steps based on validation results."""
        if validation.allowed:
            if validation.policy_mode == PolicyMode.SUGGEST_ONLY:
                return [
                    "Review the suggested remediation plan",
                    "Manually implement changes if approved",
                    "Monitor system after manual application",
                    "Update incident status upon resolution",
                ]
            elif validation.policy_mode == PolicyMode.PR_ONLY:
                return [
                    "Create pull request with proposed changes",
                    "Request code review from team lead",
                    "Run CI/CD pipeline validation",
                    "Merge after approval and monitor",
                ]
            elif validation.policy_mode == PolicyMode.GUARDED_APPLY:
                return [
                    "Remediation approved for automatic execution",
                    "Monitor system health during application",
                    "Verify resolution using test plan",
                    "Execute rollback if issues arise",
                ]
        else:
            steps = ["Remediation blocked by policy:"]
            steps.extend(f"  - {action}" for action in validation.required_actions)
            steps.extend(["Address policy violations and retry", "Contact SRE team if manual intervention needed"])
            return steps

        return ["Review recommendation and proceed according to policy"]

    async def get_policy_summary(self) -> Dict[str, Any]:
        """Get current trust gate policy configuration."""
        return self.trust_gate.get_policy_summary()

    async def update_policy_mode(self, mode: PolicyMode) -> None:
        """Update remediation policy mode at runtime."""
        current_policy = self.trust_gate.policy
        current_policy.mode = mode
        self.trust_gate.update_policy(current_policy)
        logger.info(f"Updated policy mode to: {mode.value}")

    # Legacy compatibility method
    async def remediate_incident_legacy(self, incident: dict, context_path: Path) -> bool:
        """Legacy method for backward compatibility - returns simple boolean."""
        recommendation = await self.remediate_incident(incident, context_path)
        return recommendation.allowed and recommendation.confidence > 0.5
