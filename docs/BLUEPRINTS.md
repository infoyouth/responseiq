# Blueprints

This document explains how to author remediation blueprints for ResponseIQ and how to reload them at runtime.

Location
--------
Place blueprint files under `src/blueprints/` in either YAML (`.yml`/`.yaml`) or JSON (`.json`) format. The app will load all files in that directory at startup.

Minimal fields
--------------
- `id` (string): a unique slug identifier
- `title` (string)
- `incident_signature` (string): the incident name this blueprint matches (e.g., CrashLoopBackOff)
- `severity` (string): low|medium|high
- `description` (string)
- `rationale` (string)
- `confidence` (float 0-1)
- `blast_radius` (string)
- `actions` (list): steps to propose (type, target, patch)
- `rollback` (list): steps to rollback the change

Example
-------
See `src/blueprints/crashloop_increase_memory.yml` for a canonical example.

Reloading
---------
To reload blueprints at runtime (useful during demos), call the admin endpoint:

POST /blueprints/reload

If the environment variable `BLUEPRINT_RELOAD_TOKEN` is set, include header `X-Admin-Token` with that token to authorize the reload.

Security
--------
Blueprints are proposals only. Under no circumstances does the application automatically execute actions from a blueprint. Actions are intended to be presented to a human via Slack/PR flows for approval before execution.
