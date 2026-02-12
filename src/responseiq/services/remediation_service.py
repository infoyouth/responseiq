from pathlib import Path

from responseiq.ai.llm_service import analyze_with_llm
from responseiq.utils.k8s_patcher import KubernetesPatcher
from responseiq.utils.logger import logger


class RemediationService:
    def __init__(self):
        self.k8s_patcher = KubernetesPatcher()

    async def remediate_incident(self, incident: dict, context_path: Path) -> bool:
        """
        Main entrypoint for applying a fix based on the incident type.
        Now purely AI-driven:
        1. Analyzes the incident log/reason using LLM.
        2. If a remediation is suggested, it prepares a patch (Proposed).
        """
        logger.info("Starting AI-driven remediation...")

        # Extract relevant details to send to the AI
        log_content = incident.get("log_content") or incident.get("reason") or "No log provided"

        # Call the AI Service
        # This is the "continuous" engine - it handles ANY error type provided
        # the model understands it.
        analysis_result = await analyze_with_llm(log_content)

        if not analysis_result:
            logger.warning("AI Analysis failed or was skipped (API Key missing?). " "Could not remediate.")
            return False

        remediation_plan = analysis_result.get("remediation")
        title = analysis_result.get("title", "Unknown Issue")

        if not remediation_plan:
            logger.info(f"AI analyzed '{title}' but provided no specific remediation steps.")
            return False

        logger.info(f"AI Suggested Remediation for '{title}': {remediation_plan}")

        # TODO: FUTURE: Parse the 'remediation_plan' into structured YAML edits.
        # For now, we return True to indicate we successfully identified a fix strategy,
        # even if we haven't physically applied a patch file yet.
        return True
