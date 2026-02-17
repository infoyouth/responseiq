"""
Shadow Analytics Service for P2.1 - Management Gold.

Runs proof-oriented remediation analysis on ALL incidents (even low-impact ones)
without applying fixes, generating "Projected Value Reports" for enterprise adoption.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from responseiq.schemas.proof import ProofBundle
from responseiq.services.remediation_service import RemediationService
from responseiq.services.reproduction_service import ReproductionService
from responseiq.utils.logger import logger


class ShadowAnalyticsResult:
    """Result of shadow mode analysis for a single incident."""

    def __init__(
        self,
        incident_id: str,
        would_trigger_p2: bool,
        analysis_success: bool,
        projected_fix_time: Optional[float] = None,
        confidence_score: Optional[float] = None,
        proof_bundle: Optional[ProofBundle] = None,
    ):
        self.incident_id = incident_id
        self.would_trigger_p2 = would_trigger_p2
        self.analysis_success = analysis_success
        self.projected_fix_time = projected_fix_time  # Minutes saved if auto-applied
        self.projected_fix_time_minutes = projected_fix_time  # Alias for demo compatibility
        self.confidence_score = confidence_score or 0.0
        self.value_score = min(10, (confidence_score or 0.0) * 10)  # Scale to 0-10
        self.risk_assessment = (
            "LOW" if (confidence_score or 0.0) > 0.8 else ("MEDIUM" if (confidence_score or 0.0) > 0.5 else "HIGH")
        )
        self.proof_bundle = proof_bundle
        self.analyzed_at = datetime.now()
        self.shadow_mode = True  # Always true for shadow analysis
        self.reasoning = (
            f"Shadow analysis completed with {self.confidence_score:.2f} confidence. Risk: {self.risk_assessment}."
        )
        self.automation_candidate = self.analysis_success and self.confidence_score > 0.7

    def dict(self):
        """Convert to dictionary for serialization."""
        return {
            "incident_id": self.incident_id,
            "would_trigger_p2": self.would_trigger_p2,
            "analysis_success": self.analysis_success,
            "projected_fix_time": self.projected_fix_time,
            "projected_fix_time_minutes": self.projected_fix_time_minutes,
            "confidence_score": self.confidence_score,
            "value_score": self.value_score,
            "risk_assessment": self.risk_assessment,
            "shadow_mode": self.shadow_mode,
            "reasoning": self.reasoning,
            "automation_candidate": self.automation_candidate,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


class ProjectedValueReport:
    """Management-ready report showing AI remediation potential."""

    def __init__(self, period_start: datetime, period_end: datetime):
        self.period_start = period_start
        self.period_end = period_end
        self.total_incidents_analyzed = 0
        self.p2_eligible_incidents = 0
        self.successful_analyses = 0
        self.projected_time_saved_hours = 0.0
        self.average_confidence = 0.0
        self.shadow_success_rate = 0.0
        self.incident_breakdown: Dict[str, int] = {}

    def add_result(self, result: ShadowAnalyticsResult) -> None:
        """Add a shadow analysis result to the report."""
        self.total_incidents_analyzed += 1

        if result.would_trigger_p2:
            self.p2_eligible_incidents += 1

        if result.analysis_success:
            self.successful_analyses += 1
            if result.projected_fix_time:
                self.projected_time_saved_hours += result.projected_fix_time / 60

    @property
    def potential_manual_toil_saved(self) -> str:
        """Calculate human-readable time savings."""
        hours = int(self.projected_time_saved_hours)
        minutes = int((self.projected_time_saved_hours - hours) * 60)
        return f"{hours}.{minutes} hours"

    @property
    def period_days(self) -> int:
        """Number of days in the reporting period."""
        try:
            delta = self.period_end - self.period_start
            return max(0, delta.days)
        except Exception:
            return 0

    @property
    def total_incidents(self) -> int:
        """Total incidents analyzed (alias for compatibility)."""
        return self.total_incidents_analyzed

    def dict(self) -> Dict[str, Any]:
        """Serialize report to plain dict for JSON/CLI output."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_days": self.period_days,
            "total_incidents": self.total_incidents_analyzed,
            "automation_candidates": self.automation_candidates,
            "projected_annual_savings": self.projected_annual_savings,
            "avg_time_saved_minutes": self.avg_time_saved_minutes,
            "roi_projection": self.roi_projection,
            "executive_summary": self.generate_executive_summary(),
        }

    @property
    def executive_summary(self) -> str:
        """Convenience property for templates/tests."""
        return self.generate_executive_summary()

    @property
    def automation_candidates(self) -> int:
        """Incidents that could be automatically fixed."""
        return self.successful_analyses

    @property
    def projected_annual_savings(self) -> float:
        """Projected annual cost savings in dollars."""
        sre_hourly_cost = 150  # $150/hour including overhead
        monthly_savings = self.projected_time_saved_hours * sre_hourly_cost
        return monthly_savings * 12  # Annualize

    @property
    def avg_time_saved_minutes(self) -> float:
        """Average time saved per incident in minutes."""
        if self.total_incidents_analyzed == 0:
            return 0.0
        return (self.projected_time_saved_hours * 60) / self.total_incidents_analyzed

    @property
    def roi_projection(self) -> float:
        """Return a simple ROI indicator (0-1) representing shadow success rate.

        Tests and CLI expect a numeric ROI value that can be formatted as a
        percentage. For management-level details, use `dict()` on the report.
        """
        if self.total_incidents_analyzed == 0:
            return 0.0

        # Use shadow success rate as a conservative ROI proxy
        return float(self.shadow_success_rate)

    def generate_executive_summary(self) -> str:
        """Generate executive summary for C-level presentation."""
        roi = self.roi_projection
        return f"""
ResponseIQ Shadow Mode Analysis - Executive Summary

Period: {self.period_start.strftime("%Y-%m-%d")} to {self.period_end.strftime("%Y-%m-%d")}

PROJECTED VALUE:
  - Manual Toil Saved: {self.potential_manual_toil_saved}
  - Cost Savings: ${self.projected_annual_savings:,.2f}
  - Auto-Fix Success Rate: {roi:.1%}

ADOPTION READINESS:
  - Total Incidents: {self.total_incidents_analyzed}
  - AI-Fixable: {self.successful_analyses} incidents
  - P2 Trust Level: {"HIGH" if self.shadow_success_rate > 0.9 else "MEDIUM"}

RECOMMENDATION:
  - Enable auto-apply for {self.successful_analyses} incident types to realize immediate productivity gains.
""".strip()


class ShadowAnalyticsService:
    """
    Main shadow analytics engine.

    Runs P2 analysis on ALL incidents without applying fixes,
    generating management-ready value reports.
    """

    def __init__(self):
        self.remediation_service = RemediationService()
        self.reproduction_service = ReproductionService()
        self.shadow_results: List[ShadowAnalyticsResult] = []

    async def analyze_incident_shadow(self, incident: Any) -> ShadowAnalyticsResult:
        """
        Run shadow P2 analysis on a single incident.

        Args:
            incident: Incident data (object or dict) with id, severity, description, etc.

        Returns:
            ShadowAnalyticsResult with projected value metrics
        """
        incident_id = incident.id if hasattr(incident, "id") else f"shadow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🔍 Shadow analysis starting for incident: {incident_id}")

        try:
            # Calculate if this would normally trigger P2 (impact >= 40)
            impact_score = getattr(incident, "impact_score", 0)
            would_trigger_p2 = impact_score >= 40

            # Run full P2 analysis regardless of impact score
            # This is the "shadow" part - analyze everything

            # Simulate running the full remediation workflow
            analysis_result = await self._run_shadow_remediation(incident)

            # Calculate projected fix time (how long manual fix would take)
            projected_fix_time = self._estimate_manual_fix_time(incident, analysis_result)

            result = ShadowAnalyticsResult(
                incident_id=incident_id,
                would_trigger_p2=would_trigger_p2,
                analysis_success=analysis_result is not None,
                projected_fix_time=projected_fix_time,
                confidence_score=analysis_result.get("confidence", 0.0) if analysis_result else 0.0,
            )

            self.shadow_results.append(result)
            logger.info(f"✅ Shadow analysis complete: {incident_id} (success={result.analysis_success})")
            return result

        except Exception as e:
            logger.warning(f"❌ Shadow analysis failed for {incident_id}: {str(e)}")
            return ShadowAnalyticsResult(
                incident_id=incident_id,
                would_trigger_p2=False,
                analysis_success=False,
            )

    async def _run_shadow_remediation(self, incident) -> Optional[Dict[str, Any]]:
        """Run remediation analysis without applying changes."""
        try:
            # Convert Pydantic model to dict for remediate_incident
            if hasattr(incident, "model_dump"):
                incident_dict = incident.model_dump()
            elif hasattr(incident, "dict"):
                incident_dict = incident.dict()
            else:
                incident_dict = {"id": getattr(incident, "id", "unknown")}

            # Handle enum serialization (legacy support)
            if "severity" in incident_dict and hasattr(incident_dict["severity"], "value"):
                incident_dict["severity"] = incident_dict["severity"].value

            # This simulates the full P2 workflow but doesn't apply anything
            recommendation = await self.remediation_service.remediate_incident(incident_dict)
            # Shadow analytics must *return* the analysis even when the Trust Gate
            # denies automatic application. Tests and reporting expect to see
            # confidence/plan metadata regardless of `allowed`.
            if recommendation:
                return {
                    "title": recommendation.title,
                    "confidence": recommendation.confidence,
                    "blast_radius": recommendation.blast_radius,
                    "remediation_plan": recommendation.remediation_plan,
                    "allowed": recommendation.allowed,
                }
            return None
        except Exception as e:
            logger.warning(f"Shadow remediation failed: {str(e)}")
            return None

    def _estimate_manual_fix_time(self, incident, analysis: Optional[Dict[str, Any]]) -> float:
        """Estimate how long manual fix would take (in minutes)."""
        if not analysis:
            return 0.0

        # Base time estimates by incident type (in minutes)
        base_times = {
            "network": 45,  # Network connectivity issues
            "filesystem": 30,  # File permission/path issues
            "permission": 25,  # Access control fixes
            "resource": 60,  # Memory/CPU resource issues
            "database": 90,  # Database connectivity/query issues
            "application": 35,  # Application logic errors
        }

        # Try to classify the incident type from description
        description = getattr(incident, "description", "").lower()
        for incident_type, base_time in base_times.items():
            if incident_type in description:
                return base_time

        # Default estimate for unknown types
        return 40.0

    async def generate_period_report(
        self, days_back: int = 7, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> ProjectedValueReport:
        """Generate value report for the last N days or specified period.

        Accepts either the (days_back=int) form OR (start_date: datetime, end_date: datetime)
        as the first two positional arguments (tests call both styles).
        """
        # Allow positional (start_date, end_date) call-style
        if isinstance(days_back, datetime) and isinstance(start_date, datetime):
            report_start = days_back
            report_end = start_date
        elif start_date and end_date:
            report_start = start_date
            report_end = end_date
        else:
            report_end = datetime.now()
            report_start = report_end - timedelta(days=days_back)

        report = ProjectedValueReport(report_start, report_end)

        # Filter results to the time period
        period_results = [r for r in self.shadow_results if report_start <= r.analyzed_at <= report_end]

        for result in period_results:
            report.add_result(result)

        # Calculate shadow success rate
        if period_results:
            successful = sum(1 for r in period_results if r.analysis_success)
            report.shadow_success_rate = successful / len(period_results)
            report.average_confidence = sum(
                r.confidence_score or 0.0 for r in period_results if r.confidence_score
            ) / len(period_results)

        return report

    def get_adoption_metrics(self) -> Dict[str, Any]:
        """Get metrics for enterprise adoption decision."""
        if not self.shadow_results:
            return {"error": "No shadow analysis data available"}

        total_results = len(self.shadow_results)
        successful_analyses = sum(1 for r in self.shadow_results if r.analysis_success)

        return {
            "total_incidents_analyzed": total_results,
            "shadow_success_rate": f"{(successful_analyses / total_results) * 100:.1f}%",
            "recommendation": "ENABLE_AUTO_APPLY" if successful_analyses / total_results > 0.8 else "CONTINUE_SHADOW",
            "confidence": "HIGH" if successful_analyses / total_results > 0.9 else "MEDIUM",
        }
