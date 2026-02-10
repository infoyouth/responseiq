import os
from pathlib import Path

from src.utils.k8s_patcher import KubernetesPatcher
from src.utils.logger import logger

# Import parser registry to map incidents to files (if we had complex mapping)
# For MVP, we will scan for deployment.yaml nearby the log or root


class RemediationService:
    def __init__(self):
        self.k8s_patcher = KubernetesPatcher()

    def remediate_incident(self, incident: dict, context_path: Path) -> bool:
        """
        Main entrypoint for applying a fix based on the incident type.
        """
        reason = incident.get("reason", "").lower()

        # 1. Deterministic Mapping: OOM -> Memory Increase
        if "panic" in reason or "oom" in reason or "memory" in reason:
            return self._apply_oom_fix(context_path)

        logger.info(f"No deterministic fix found for: {reason}")
        return False

    def _apply_oom_fix(self, root_path: Path) -> bool:
        """
        Strategy: Search for deployment.yaml in the repo and double memory.
        """
        logger.info("Applying OOM Fix: Scanning for deployment manifests...")

        # Heuristic: Find any file named deployment.yaml or values.yaml
        targets = []
        if root_path.is_file():
            root_path = root_path.parent

        for root, _, files in os.walk(root_path):
            for file in files:
                if file in ["deployment.yaml", "deployment.yml"]:
                    targets.append(Path(root) / file)

        if not targets:
            logger.warning("No deployment.yaml found to patch.")
            return False

        # Apply to all found for MVP (High blast radius but safe for playground)
        success = False
        for target in targets:
            logger.info(f"Patching {target} with increased memory limit...")
            if self.k8s_patcher.update_memory_limit(target, new_limit="1Gi"):
                logger.info(f"Successfully patched {target}")
                success = True
            else:
                logger.error(f"Failed to patch {target}")

        return success

    def create_fix_pr(self, file_patched: Path, repo: str) -> bool:
        # TODO: Link this to GitHubIntegration
        return False
