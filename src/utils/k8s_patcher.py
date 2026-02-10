import os
from pathlib import Path
from typing import Optional, Dict, Any

from ruamel.yaml import YAML

class KubernetesPatcher:
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    def load_deployment(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Safely loads a Kubernetes YAML file."""
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return self.yaml.load(f)
        except Exception:
            return None

    def save_deployment(self, file_path: Path, content: Dict[str, Any]) -> bool:
        """Saves the modified content back to the file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                self.yaml.dump(content, f)
            return True
        except Exception:
            return False

    def update_memory_limit(self, file_path: Path, container_name: str = None, new_limit: str = "512Mi") -> bool:
        """
        Updates the memory limit for a specific container or the first key container found.
        """
        data = self.load_deployment(file_path)
        if not data:
            return False

        # Navigate nested structure: spec -> template -> spec -> containers
        try:
            containers = data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            target = None
            
            if not containers:
                return False

            if container_name:
                for c in containers:
                    if c.get("name") == container_name:
                        target = c
                        break
            else:
                # Default to first container if not specified (common for single-container pods)
                target = containers[0]

            if target:
                # Ensure structure exists
                if "resources" not in target:
                    target["resources"] = {}
                if "limits" not in target["resources"]:
                    target["resources"]["limits"] = {}
                
                # Apply update
                target["resources"]["limits"]["memory"] = new_limit
                return self.save_deployment(file_path, data)
            
            return False
            
        except Exception:
            return False
