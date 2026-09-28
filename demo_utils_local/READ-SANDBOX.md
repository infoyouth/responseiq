# ResponseIQ Local Sandbox

**Local-only end-to-end test framework. Never pushed to remote (`sandbox/` is in `.gitignore`).**

Run everything: `make sand`  
First-time setup for GitHub repo incidents: `make sand-setup`

---

## Incidents & What They Verify

| Command | Incident | What it proves |
|---|---|---|
| `make sand-payment` | INC-001 — Payment silent failure | **P4 Guardrails**: `no_hardcoded_secrets` (BLOCK) + `no_bare_except` (DOWNGRADE) + `no_print_statements` (WARN) all fire on `payment_service.py` |
| `make sand-auth` | INC-002 — Auth KeyError + PII in logs | **P2.3 PII Scrubbing**: email, JWT, Bearer token, IP all redacted from `auth_crash.log` before reaching the LLM |
| `make sand-inventory` | INC-003 — DB connection pool exhausted | **P4 Guardrails**: `no_direct_os_system` (BLOCK) + `no_mutable_default_args` (DOWNGRADE) fire on `inventory_service.py` |
| `make sand-fastapi` | INC-004 — FastAPI template `deps.py:21` | **P2.4 Multi-Repo**: resolver walks `sandbox/repos/full-stack-fastapi-template/backend/app/` to find the real crashed line; requires `make sand-setup` |
| `make sand-flask` | INC-005 — Flask 3.1.2 `stream_with_context` | **P2.4 Multi-Repo**: resolver walks `sandbox/repos/flask/src/flask/` at tag 3.1.2; requires `make sand-setup` |
| `make sand` | All 5 incidents | Full pipeline: scrub → context extract → guardrails → remediation |
| `make sand-v` | All 5 incidents | Same as above with full JSON evidence output |

---

## What Each Step Exercises

Every incident runs these 4 steps in sequence:

1. **P2.3 PII Scrubbing** *(INC-002 only)* — `scrub()` replaces email / JWT / Bearer / IP with `<REDACTED_*>` placeholders before any LLM call.
2. **P2.4 Multi-Repo Context Extraction** — `MultiRepoResolver` maps stack-trace paths (e.g. `/app/services/payment_service.py:129`) to real local source files and surfaces the crashed code block.
3. **P4 Sovereign Guardrails** *(P4 incidents only)* — `GuardrailChecker` scans the service source for violations: BLOCK halts automation, DOWNGRADE forces PR-only, WARN goes to audit trail.
4. **Full Remediation Pipeline** — `RemediationService.remediate_incident()` runs the complete `Detect → Context → Reason → Policy → Execute → Learn` state machine with local LLM fallback (no API key required).

---

## Victim Services (`sandbox/services/`)

| File | Deliberate bugs |
|---|---|
| `payment_service.py` | Hardcoded `sk-...` key (P4 BLOCK), bare `except:` (P4 DOWNGRADE), `print()` (P4 WARN), ConnectTimeout silently swallowed |
| `auth_service.py` | `_build_claims(scopes=[])` mutable default (P4), PII in log payload, `KeyError: 'last_seen'` on refresh path |
| `inventory_service.py` | `os.system()` shell call (P4 BLOCK), `reserve_items(reserved=[])` mutable default (P4 DOWNGRADE), `conn.close()` missing on early return → pool exhaustion |

---

## Real GitHub Repos (`sandbox/repos/` — after `make sand-setup`)

| Repo | Scope cloned | Incident |
|---|---|---|
| `fastapi/full-stack-fastapi-template` | `backend/app/` only (depth=1) | INC-004: `deps.py:21` sync dependency in async handler strips traceback (#13067) |
| `pallets/flask` @ tag `3.1.2` | `src/flask/` only (depth=1) | INC-005: `helpers.py:130` `stream_with_context` double-teardown (#5804) |

---

## Adding a New Incident

1. Drop a new log fixture in `sandbox/logs/my_crash.log`  
2. Optionally add a victim service in `sandbox/services/`  
3. Add an entry to the `INCIDENTS` list in `sandbox/run_demo.py`  
4. Add `make sand-myservice` to [Makefile](../Makefile) pointing to `--incident myservice`
