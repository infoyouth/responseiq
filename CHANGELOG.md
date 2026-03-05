# CHANGELOG

All notable changes to this project will be documented in this file.

This changelog is managed automatically by
[python-semantic-release](https://python-semantic-release.readthedocs.io/).
Manual edits below the latest release header will be preserved.

<!-- semantic-release: start -->

## v2.17.0 (2026-03-05)

### Features

- **PDF/CSV Pilot Report Export** — `GET /api/v1/shadow/report/export`
  Streams a `ProjectedValueReport` as a downloadable CSV (stdlib) or A4 PDF
  (fpdf2). Install the optional extra with `pip install "responseiq[reports]"`.

- **ProofBundle Persistence** — `GET /api/v1/incidents/{id}/proof`
  Seals remediation integrity hashes (`integrity_hash`, `chain_hash`,
  `pre_fix_hash`, `post_fix_hash`) to an append-only `ProofBundleRecord` table
  after every remediation cycle (Step 10 in `RemediationService`).
  Provides a durable SOC 2-aligned audit trail.

- **Post-Apply Watchdog + Auto-Rollback** — `POST /api/v1/incidents/{id}/watchdog/start`
  Async background monitor that samples the post-fix error rate for a
  configurable window (default 5 min). Triggers the pre-generated rollback
  script automatically if the error rate exceeds the threshold (default 5 %).
  Controlled by `watchdog_enabled` / `watchdog_error_threshold` /
  `watchdog_window_seconds` settings.

- **PLG samples/ folder** — `samples/buggy_service.py` + `samples/crash.log`
  Runnable 60-second zero-config demo scenario. README updated with
  "⚡ Try it in 60 seconds" section and "🔌 Compatible With" integrations table.

### Fixes

- **RC startup crash** — `pyyaml>=6.0` added as a hard runtime dependency
  (previously only `types-pyyaml` stubs were declared). `ShadowAnalyticsService`
  instantiation moved from module-level to a lazy factory in
  `routers/shadow_report.py` to prevent the full init chain running at import
  time in a clean install.

<!-- semantic-release: end -->
