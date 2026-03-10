# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Static baseline constants shared across all config environments.

Keep this file minimal — only values that never change between dev,
test, and prod belong here. Environment-specific overrides live in
``settings.py``.
"""

REMEDIATION_MAX_RETRIES = 3
