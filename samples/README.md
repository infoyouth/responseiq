# ResponseIQ — Sample Scenario

This folder gives you a **real, runnable 60-second demo** of ResponseIQ with zero setup.

---

## What is in here?

| File | Purpose |
|---|---|
| `buggy_service.py` | A deliberately broken Python service with 3 embedded bugs |
| `crash.log` | Pre-recorded crash log produced by running `buggy_service.py` |

### Bugs embedded in `buggy_service.py`

| # | Type | Location | Trigger |
|---|---|---|---|
| 1 | Memory leak | `_request_log` list, line 18 | Never pruned — grows unbounded on every call |
| 2 | `KeyError` | `user["email"]`, line 45 | OAuth-style users with no `email` field |
| 3 | `ZeroDivisionError` | `avg_payload` line, line 57 | Race between `process_user_request` and `reset_counters` |

---

## Run the demo (60 seconds, no API key needed)

```bash
# 1. Install (if you haven't already)
pip install responseiq

# 2. Scan the pre-recorded crash log
responseiq --mode scan --target ./samples/crash.log

# 3. (Optional) Run shadow mode to see projected MTTR savings
responseiq --mode shadow --target ./samples/ --shadow-report
```

Expected output from step 2:

```
------------------------------------------------------------
  ResponseIQ Scan Report
  Target : samples/crash.log
  Status : SUCCESS
------------------------------------------------------------
  Scanned  : 3 message(s)
  Incidents: 3 found
------------------------------------------------------------
  1. [HIGH]     KeyError: 'email' in process_user_request
  2. [CRITICAL] Memory leak — _request_log unbounded growth
  3. [HIGH]     ZeroDivisionError: division by zero (reset_counters race)
------------------------------------------------------------
  Tip: run with --mode fix to apply safe remediations.
------------------------------------------------------------
```

> **No LLM key required.** ResponseIQ uses its built-in rule-engine fallback
> when no `OPENAI_API_KEY` or `LLM_BASE_URL` is configured.

---

## Reproduce the crashes yourself

```bash
python samples/buggy_service.py
```

This will print the same stack traces that `crash.log` was generated from.
