# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""YAML prompt loader and Jinja2 template renderer.

Loads node prompt templates from ``prompts/node_prompts.yaml`` and
exposes ``render_prompt`` for injecting runtime values (incident
details, patch context) into prompt strings before LLM calls.
"""

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
