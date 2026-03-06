# ResponseIQ — Benchmark Baseline

> Fixture-based performance baseline for the ResponseIQ remediation pipeline.
> Measured against `fixtures/` dataset. Updated per release.
>
> **Methodology**: Each fixture is submitted to `responseiq --mode scan` against a local Ollama `llama3.2` model on an M2 MacBook Pro / AMD Ryzen 9 7950X Linux workstation. Metrics are wall-clock times captured via `time` and Python `perf_counter`. Averages over 5 independent runs.

---

## Fixture Dataset

| Fixture | Log Message | Expected Severity |
|---|---|---|
| `fixture_high.json` | `panic: out of memory while allocating buffer` | `high` |
| `fixture_medium.json` | `error: failed to connect to upstream service (timeout)` | `medium` |
| `fixture_none.json` | `informational: background job completed successfully` | `None` (filtered) |

---

## Severity Classification Accuracy

| Fixture | Expected | Actual | Pass |
|---|---|---|---|
| `fixture_high.json` | `high` | `high` | ✅ |
| `fixture_medium.json` | `medium` | `medium` | ✅ |
| `fixture_none.json` | `None` | — (noise-filtered) | ✅ |

**Classification accuracy: 3/3 (100%)** on baseline fixture set.

---

## MTTR Delta (Time-to-First-Fix-PR)

> Time from log ingestion to GitHub PR open (dry-run mode — no real PR created).

| Severity | p50 | p95 | Notes |
|---|---|---|---|
| HIGH / CRITICAL | ~18 s | ~34 s | Includes Tree-sitter AST context extraction + LLM reasoning |
| MEDIUM | ~12 s | ~22 s | Reduced context window — fewer source files loaded |
| LOW / INFO | < 1 s | < 1 s | Noise-filtered before reaching LLM |

> Baseline measured with **Ollama `llama3.2` (local)**. Cloud LLM backends (OpenAI GPT-4o) are typically 2–4× faster due to batch throughput but incur network latency.

---

## LLM Call Latency

| Stage | Model | p50 | p95 |
|---|---|---|---|
| Triage / Classification | `llama3.2` | 1.8 s | 4.2 s |
| Remediation reasoning | `llama3.2` | 8.4 s | 18.6 s |
| Trust Gate validation | Rule-based (no LLM) | < 5 ms | < 5 ms |

> Token counts: triage prompt ≈ 512 tokens; remediation prompt ≈ 2 048–4 096 tokens (varies with AST context depth).

---

## Trust Gate Acceptance Rate

> Proportion of AI-generated patches that pass all 7 Trust Gate guardrails without requiring human override.

| Fixture Set | Passed | Blocked | Acceptance Rate |
|---|---|---|---|
| `fixture_high.json` | 5/5 | 0/5 | 100% |
| `fixture_medium.json` | 5/5 | 0/5 | 100% |
| Synthetic adversarial (secrets injected) | 0/5 | 5/5 | 0% (correct block) |

> Adversarial fixtures are internal test vectors — not in the public `fixtures/` directory.

---

## Noise Filter Effectiveness

| Total log lines (test corpus) | Lines passed to LLM | Lines filtered | Filter rate |
|---|---|---|---|
| 1 000 | 47 | 953 | 95.3% |

High filter rate intentional — only anomalous, error-level, and severity-tagged lines are forwarded to the LLM pipeline.

---

## CI Performance

| Metric | Value |
|---|---|
| Test suite size | 660+ tests |
| CI wall-clock (single worker) | ~4 min 20 s |
| CI wall-clock (`pytest-xdist -n auto`, 4 workers) | ~1 min 45 s |
| Speedup | ~2.5× |

---

## Reproduction

```bash
# Run the fixture benchmark yourself
uv run responseiq --mode scan --target fixtures/fixture_high.json
uv run responseiq --mode scan --target fixtures/fixture_medium.json
uv run responseiq --mode scan --target fixtures/fixture_none.json
```

> Requires a local Ollama instance (`ollama serve`) or a valid `RESPONSEIQ_OPENAI_API_KEY`.
> See [README.md](README.md) for full setup instructions.

---

*Last updated: v2.19.2 — March 2026*
