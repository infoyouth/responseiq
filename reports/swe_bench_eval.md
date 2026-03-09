# ResponseIQ × SWE-bench Verified — Evaluation Report

> Dataset: [princeton-nlp/SWE-bench_Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified)  
> Samples evaluated: **20**

## Summary

| Metric | Value |
|---|---|
| **Pass@1 (heuristic)** | **20.0%** |
| Total samples | 20 |
| Passed | 4 |
| Trust Gate blocked | 1 |
| Errors | 0 |
| Avg latency | 29.1s |
| Avg confidence | 57.0% |

> **Note:** Pass@1 here uses a lightweight heuristic (non-empty patch, Trust Gate
> approved, causal symbol overlap). A full evaluation requires applying the patch
> to a cloned repo and running the failing tests — see `--full-eval` (requires Docker).

## Per-Repo Breakdown

| Repo | Samples | Passed | Pass rate |
|---|---|---|---|
| `example/auth-service` | 2 | 0 | 0% |
| `example/recommendation-engine` | 1 | 1 | 100% |
| `example/event-bus` | 1 | 0 | 0% |
| `example/ingestion-worker` | 1 | 0 | 0% |
| `example/billing-service` | 1 | 0 | 0% |
| `example/analytics-export` | 1 | 0 | 0% |
| `example/notification-svc` | 1 | 0 | 0% |
| `example/config-loader` | 1 | 0 | 0% |
| `example/file-processor` | 1 | 0 | 0% |
| `example/order-service` | 1 | 0 | 0% |
| `example/cache-layer` | 1 | 0 | 0% |
| `example/ml-serving` | 1 | 1 | 100% |
| `example/job-scheduler` | 1 | 1 | 100% |
| `example/metrics-svc` | 1 | 1 | 100% |
| `example/stream-processor` | 1 | 0 | 0% |
| `example/api-gateway` | 1 | 0 | 0% |
| `example/session-service` | 1 | 0 | 0% |
| `example/tree-parser` | 1 | 0 | 0% |
| `example/data-pipeline` | 1 | 0 | 0% |

## Per-Instance Results (first 50)

| Instance | Repo | Pass | Conf | Latency | Trust Gate | Error |
|---|---|---|---|---|---|---|
| `fixture-006` | `example/recommendation-engine` | ✅ | 60% | 34.5s | ✅ |  |
| `fixture-020` | `example/event-bus` | ❌ | 60% | 35.8s | ✅ |  |
| `fixture-015` | `example/ingestion-worker` | ❌ | 60% | 35.5s | ✅ |  |
| `fixture-005` | `example/billing-service` | ❌ | 60% | 30.1s | ✅ |  |
| `fixture-010` | `example/analytics-export` | ❌ | 0% | 31.1s | 🚫 |  |
| `fixture-014` | `example/notification-svc` | ❌ | 60% | 31.5s | ✅ |  |
| `fixture-007` | `example/config-loader` | ❌ | 60% | 22.7s | ✅ |  |
| `fixture-016` | `example/file-processor` | ❌ | 60% | 28.2s | ✅ |  |
| `fixture-019` | `example/order-service` | ❌ | 60% | 28.3s | ✅ |  |
| `fixture-013` | `example/cache-layer` | ❌ | 60% | 36.8s | ✅ |  |
| `fixture-018` | `example/ml-serving` | ✅ | 60% | 36.0s | ✅ |  |
| `fixture-011` | `example/job-scheduler` | ✅ | 60% | 36.2s | ✅ |  |
| `fixture-002` | `example/metrics-svc` | ✅ | 60% | 28.7s | ✅ |  |
| `fixture-012` | `example/stream-processor` | ❌ | 60% | 28.0s | ✅ |  |
| `fixture-003` | `example/api-gateway` | ❌ | 60% | 27.9s | ✅ |  |
| `fixture-017` | `example/auth-service` | ❌ | 60% | 25.7s | ✅ |  |
| `fixture-008` | `example/session-service` | ❌ | 60% | 25.5s | ✅ |  |
| `fixture-009` | `example/tree-parser` | ❌ | 60% | 25.3s | ✅ |  |
| `fixture-001` | `example/auth-service` | ❌ | 60% | 14.0s | ✅ |  |
| `fixture-004` | `example/data-pipeline` | ❌ | 60% | 19.7s | ✅ |  |

---

## How to Run a Full Evaluation

The heuristic Pass@1 above is a fast proxy. For the gold-standard evaluation:

```bash
# 1. Install SWE-bench evaluation harness
pip install swebench

# 2. Generate predictions file from ResponseIQ
uv run python scripts/swe_bench_eval.py --samples 500 --output-predictions predictions.jsonl

# 3. Run official SWE-bench evaluator (requires Docker)
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path predictions.jsonl \
    --run_id responseiq_eval \
    --instance_ids all
```

_For CI/CD integration, use `--dry-run` for fast smoke tests on every PR._
