import os
from typing import Any, Dict

import yaml
from jinja2 import Template

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "../prompts/node_prompts.yaml")


def load_prompts() -> Dict[str, Any]:
    with open(PROMPT_PATH, "r") as f:
        return yaml.safe_load(f)


def render_prompt(template_str: str, **kwargs) -> str:
    template = Template(template_str)
    return template.render(**kwargs)


# Usage:
# prompts = load_prompts()
# prompt = render_prompt(prompts['critique_node'], logs=..., patch=..., retry_count=...)
