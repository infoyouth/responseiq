"""
Remediation Service with Trust Gate Integration
Enterprise-ready remediation with policy enforcement, safety checks, and structured outputs.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from responseiq.ai.llm_service import analyze_with_llm
from responseiq.config.policy_config import PolicyMode
from responseiq.schemas.causal_graph import CausalGraph
from responseiq.schemas.proof import ProofBundle, ReproductionStatus
from responseiq.services.causal_graph_service import build_causal_graph
from responseiq.services.git_correlation_service import CorrelationResult, GitCorrelationService
from responseiq.services.impact import assess_impact
from responseiq.services.performance_gate import PerformanceGateResult, gate as _perf_gate, measure_latency
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
    correlation: Optional[CorrelationResult] = None  # P3: Git change-to-incident correlation
    causal_graph: Optional[CausalGraph] = None  # P6: Causal root-cause graph

    # P5.3: LLM audit trail — which model was used for this analysis
    llm_model_used: Optional[str] = None

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
            "proof_bundle": (
                asdict(self.proof_bundle) if self.proof_bundle else None
            ),  # P2: Include proof in audit trail
            "proof_integrity": (
                {
                    "integrity_hash": self.proof_bundle.integrity.integrity_hash,
                    "chain_hash": self.proof_bundle.integrity.chain_hash,
                    "algorithm": self.proof_bundle.integrity.algorithm,
                    "sealed_at": (
                        self.proof_bundle.integrity.sealed_at.isoformat()
                        if self.proof_bundle.integrity.sealed_at
                        else None
                    ),
                    "chain_verified": self.proof_bundle.integrity.chain_verified,
                    "tamper_proof": self.proof_bundle.integrity.tamper_proof,
                }
                if self.proof_bundle and self.proof_bundle.integrity and self.proof_bundle.integrity.integrity_hash
                else None
            ),  # P2 Integrity Gate: forensic SHA-256 chain for SOC2/compliance
            "correlation": (self.correlation.to_dict() if self.correlation else None),  # P3: Git correlation result
            "causal_graph": (self.causal_graph.to_dict() if self.causal_graph else None),  # P6: causal chain
            "llm_model_used": self.llm_model_used,  # P5.3: audit trail
        }


class RemediationService:
    """
    Enterprise-grade remediation service with Trust Gate integration.
    Provides safe, policy-governed, explainable incident remediation.
    """

    def __init__(self, environment: str = "production", repo_path: Optional[Path] = None):
        self.k8s_patcher = KubernetesPatcher()
        self.trust_gate = TrustGateValidator(environment=environment)
        self.reproduction_service = ReproductionService()  # P2: Proof-oriented testing
        self.rollback_generator = ExecutableRollbackGenerator()  # P2.1: Executable rollbacks
        self.git_correlation = GitCorrelationService(repo_path=repo_path)  # P3: Change correlation
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

        # Step 2: AI analysis for remediation plan (P5: timed for performance gate)
        async with measure_latency(_perf_gate, "analyze_incident", phase="rolling"):
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

        # Step 2.5: P3 — Git change-to-incident correlation
        correlation = None
        try:
            correlation = await self.git_correlation.correlate(log_text=log_content, lookback_hours=24)
            if correlation.suspect_commit:
                logger.info(
                    f"P3 correlation: suspect='{correlation.suspect_commit}' "
                    f"confidence={correlation.confidence_score:.2f} method={correlation.method}"
                )
            else:
                logger.debug("P3 correlation: no suspect commit identified")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Git correlation failed (non-fatal): {exc}")

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

                    # P2.1 Sovereign Audit: Execute "Negative Proof" (Pre-fix validation)
                    # We run the test immediately to prove failure before any remediation is applied.
                    logger.info(f"🔬 Executing Negative Proof test: {proof_bundle.reproduction_test.test_path}")
                    proof_bundle = await self.reproduction_service.execute_reproduction_test(proof_bundle)

                    if proof_bundle.pre_fix_evidence:
                        logger.info("📉 Negative Proof captured (Test failed as expected)")
                        # Seal the evidence immediately for audit trail
                        proof_bundle.seal_forensic_evidence()
                    else:
                        logger.warning("❓ Negative Proof failed: Test passed unexpectedly or errored")

                else:
                    logger.warning("⚠️  Reproduction test generation completed but no test was created")
            except Exception as e:
                logger.warning(f"⚠️  Failed to generate reproduction test: {str(e)}")

        # Step 3.6: P5 — Performance regression gate
        # Evaluate whether analysis latency regressed vs baseline (if any baseline exists).
        perf_result: PerformanceGateResult = _perf_gate.evaluate("analyze_incident")
        if proof_bundle is not None:
            proof_bundle.perf_gate_result = perf_result
        if not perf_result.passed:
            logger.warning(
                "⚠️  PERFORMANCE GATE FAIL: %s",
                perf_result.reason,
            )

        # Step 4: Build remediation request for trust gate
        blast_radius = impact_assessment.factors.get("affected_surface", "single_service")

        # Extract affected files and changes from AI analysis
        affected_files = analysis_result.get("affected_files", [])
        proposed_changes = analysis_result.get("proposed_changes", [])

        # Generate rollback and test plans
        rollback_plan = await self._generate_rollback_plan(analysis_result, affected_files, proposed_changes)
        test_plan = self._generate_test_plan(analysis_result, title)

        # P2: Truth in Labeling - Check proof quality before creating request
        if proof_bundle and proof_bundle.reproduction_test:
            # P2 Hardening - Strict "Successful Failure" check
            # If the reproduction test passed unexpectedly, IT'S NOT A BUG (or the test is bad).
            if proof_bundle.reproduction_test.status == ReproductionStatus.PASSED_UNEXPECTEDLY:
                logger.error(
                    "🛑 INVALID PROOF: Reproduction test passed on buggy code. Aborting autonomous remediation."
                )
                ai_confidence = 0.0  # Force failure in trust gate due to invalid proof

            # If we only have static fallback, downgrade confidence for the trust gate logic
            # This forces human approval (PR_ONLY) instead of autonomous execution.
            elif proof_bundle.reproduction_test.repro_method == "static_fallback":
                logger.warning(
                    "📉 Reproduction achieved via Static Template (Basic Path Check). "
                    "High-confidence logic verification was unavailable. Downgrading trust."
                )
                # Cap confidence below typical automation thresholds (usually 0.8+)
                ai_confidence = min(ai_confidence, 0.5)

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

        # P2 Policy Enforcement: Downgrade execution mode if proof is weak
        if (
            validation_result.allowed
            and validation_result.policy_mode == PolicyMode.GUARDED_APPLY
            and proof_bundle
            and proof_bundle.reproduction_test
            and proof_bundle.reproduction_test.repro_method == "static_fallback"
        ):
            logger.warning("🛡️ TRUST GATE OVERRIDE: Downgrading to PR_ONLY due to static_fallback proof.")
            validation_result.policy_mode = PolicyMode.PR_ONLY
            validation_result.message += (
                " | TRUST GATE: Reproduction achieved via Static Template (Basic Path Check). "
                "High-confidence logic verification was unavailable. Downgrading to PR_ONLY."
            )

        # P5 Policy Enforcement: Downgrade execution mode on latency regression
        if (
            not perf_result.passed
            and validation_result.allowed
            and validation_result.policy_mode == PolicyMode.GUARDED_APPLY
        ):
            logger.warning(
                "\U0001f6a6 PERF GATE OVERRIDE: Downgrading to PR_ONLY due to latency regression. %s",
                perf_result.reason,
            )
            validation_result.policy_mode = PolicyMode.PR_ONLY
            validation_result.message += (
                f" | PERF GATE: Latency regression detected (+{perf_result.delta_pct:.1f}%). "
                "Autonomous apply blocked until regression is investigated."
            )

        # P2 Integrity Gate v2.15.0: populate post_fix_evidence and re-seal with full pre+post context.
        # The validation result (security scan, policy checks) constitutes the "post-fix" proof
        # artifact: it shows the fix was validated before any production apply.
        if proof_bundle is not None:
            if proof_bundle.post_fix_evidence is None:
                import json as _json

                proof_bundle.post_fix_evidence = _json.dumps(
                    {
                        "checks_passed": validation_result.checks_passed,
                        "checks_failed": validation_result.checks_failed,
                        "policy_mode": validation_result.policy_mode.value if validation_result.policy_mode else None,
                        "allowed": validation_result.allowed,
                        "security_scan": proof_bundle.security_scan_output or "n/a",
                    },
                    sort_keys=True,
                )
            # Re-seal with both pre+post evidence — produces chain_hash + integrity_hash
            proof_bundle.seal_forensic_evidence()
            if proof_bundle.integrity and proof_bundle.integrity.integrity_hash:
                logger.info(
                    "\U0001f512 Integrity Gate: evidence sealed",
                    integrity_hash=proof_bundle.integrity.integrity_hash[:16] + "...",
                    chain_verified=proof_bundle.integrity.chain_verified,
                )

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
            correlation=correlation,  # P3: Git change-to-incident correlation
            llm_model_used=analysis_result.get("llm_model_used"),  # P5.3: audit trail
        )

        # Step 7: Add risk assessment
        recommendation.risk_assessment = self._assess_remediation_risk(
            validation_result, impact_assessment, analysis_result
        )

        # Step 8: Generate next steps based on validation result
        recommendation.next_steps = self._generate_next_steps(validation_result, recommendation)

        # Step 9: P6 — Build causal root-cause graph from all pipeline signals
        recommendation.causal_graph = build_causal_graph(
            incident_id=incident_id,
            analysis_result=analysis_result,
            correlation=correlation,
            impact_score=impact_assessment.score,
            perf_result=perf_result,
            proof_bundle=proof_bundle,
        )

        # Step 10: #2 v2.18.0 — Persist sealed ProofBundle to DB (SOC2 audit trail)
        if proof_bundle is not None and proof_bundle.integrity and proof_bundle.integrity.integrity_hash:
            from responseiq.services.proof_persistence_service import persist_proof_bundle as _persist_proof

            await _persist_proof(incident_id=incident_id, proof_bundle=proof_bundle)

        # Log final decision
        if validation_result.allowed:
            logger.info(f"✅ Remediation APPROVED for {incident_id}: {validation_result.message}")
        else:
            logger.warning(f"❌ Remediation DENIED for {incident_id}: {validation_result.message}")

            # P2 Cleanup: If remediation is denied, we don't need the proof artifact anymore.
            if proof_bundle:
                await self.reproduction_service.cleanup_reproduction_test(proof_bundle)

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
