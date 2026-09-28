# ResponseIQ Consolidated Next Plan

## Product Direction

Make ResponseIQ an open-source, evidence-driven remediation control plane:

> Connect incident signals to repository-aware diagnosis, validated patches,
> policy decisions, rollback, and an auditable outcome record.

ResponseIQ owns orchestration, Trust Gate policy, evidence levels, and
ProofBundle integrity. It composes mature tools for telemetry, source analysis,
isolation, and deployment integrations.

The near-term product position is **review-first remediation copilot**, not
autonomous self-healing production software. Stronger claims require the gates
and measurements defined below.

## Engineering Principles

- **Fail closed:** unavailable, timed-out, or unknown validation is not success.
- **Least privilege:** generated code receives no host credentials or network
  access unless policy explicitly grants it.
- **Reproducibility:** every result includes inputs, tools, versions, commands,
  environment, and outputs needed to repeat it.
- **Small reversible changes:** each pull request has one objective, focused
  tests, and a rollback path.
- **Evidence before confidence:** model confidence never upgrades evidence level
  by itself.
- **Human control:** production changes require explicit human approval.
- **Measured delivery:** a phase is complete only when its exit gate passes.

“Never fail” is not an achievable software guarantee. The practical target is
to contain failures, detect them early, preserve evidence, and prevent an
uncertain system from taking a higher-risk action.

## Phase 0 — Claims, Baseline, and Measurement

Establish a truthful baseline before adding new capability.

### Requirements

- Describe the product as review-first remediation until later gates pass.
- Describe SHA-256 as artifact integrity, not causal proof or SOC2 readiness.
- Separate synthetic fixtures from official benchmark results.
- Define a 100-incident replay corpus with expected root cause, target files,
  expected validation, and outcome labels.
- Record baseline triage accuracy, patch application rate, test-pass rate, false
  positives, false negatives, latency, cost, rollback success, and evidence
  completeness.
- Use a failure taxonomy: missing context, wrong diagnosis, invalid patch,
  validation failure, sandbox failure, policy block, and infrastructure error.

### Exit gate

README and security claims match observable implementation, and another
developer can reproduce the baseline dataset and measurement procedure.

## Phase 1 — Fail-Closed Safety and Policy

Make the Trust Gate and normal CLI path safe before improving intelligence.

### Requirements

- Missing security or test executables fail validation.
- Test errors, timeouts, and unavailable environments fail validation or force
  human review.
- Unknown check types fail configuration validation.
- Required checks run against the candidate patch, not the caller checkout.
- Load `RESPONSEIQ_POLICY_MODE` consistently in every entry point.
- Make the documented default match runtime behavior; production defaults to
  `pr_only`.
- Ensure guarded apply has an explicit, auditable opt-in.
- Add tests for missing tools, failures, timeouts, unknown checks, and policy
  modes.

### Exit gate

No required check reports success without successful execution against the
candidate change. A policy matrix proves no default path applies or merges a
production change without explicit approval.

## Phase 2 — Source-Grounded Triage and Bounded Context

Make diagnosis use the same source context throughout the pipeline.

### Requirements

- Group duplicate log lines into incidents using deterministic fingerprints.
- Rank probable root causes before remediation.
- Extract source context once and pass it through triage, remediation, and
  reproduction generation.
- Expand context from the stack-frame function to direct imports, callers,
  callees, interfaces, configuration, and tests.
- Rank context with AST proximity and Git recency while keeping direct
  dependencies above zero priority.
- Link every claim to a log line, symbol, recent change, or executable check.
- Record unresolved source references in the ProofBundle.

Use Tree-sitter and `ast-grep` first. Do not build a full dependency graph or
custom incident database before measurement proves the need.

### Exit gate

An end-to-end test proves a stack trace target reaches the LLM prompt,
reproduction generator, and proof record. Duplicate events produce one
incident with stable evidence references.

## Phase 3 — Sandboxed Reproduction and Candidate Validation

Turn validation into a trustworthy, bounded execution process.

### Requirements

- Never execute LLM-generated Python directly on the host.
- Use a disposable sandbox or container with network and host credentials
  disabled by default.
- Enforce CPU, memory, process, disk, and wall-clock limits.
- Isolate worktree, build outputs, databases, caches, and test artifacts for
  every attempt.
- Apply the candidate patch only in the isolated environment.
- Run the real reproduction path, focused tests, type checks, and security
  checks against that candidate.
- Require the expected exception or incident signature, not merely exit code 1.
- Run post-fix reproduction as part of the actual remediation workflow.
- Downgrade evidence and require PR-only review when real application behavior
  cannot be exercised.

Use Git worktrees for lightweight validation and Dagger or Testcontainers when
service-level isolation is required. Share only immutable dependency caches.

### Exit gate

Adversarial tests prove generated validation code cannot access host secrets,
modify the caller checkout, escape resource limits, or gain unrestricted
network access. A real target-code regression passes before and after in a
clean environment.

## Phase 4 — ProofBundle Integrity and Causal Evidence

Make evidence precise, complete, and honest about what it proves.

### Requirements

- Hash canonical incident input, source context, patch, validation commands,
  outputs, policy decision, and timestamps.
- Persist the exact sealed payload, not only selected hashes and confidence
  scores.
- Implement an ordered hash chain with an explicitly persisted previous hash.
- Record evidence provenance, tool versions, exit status, environment, and
  sandbox identity.
- Separate artifact integrity, causal correctness, and validation strength.
- Use explicit levels: `synthetic_signature`, `static_validation`,
  `application_reproduction`, `integration_validation`, and
  `production_observed`.
- For `production_observed`, require:

  ```text
  elapsed_time >= 30 minutes AND request_volume >= baseline_threshold
  ```

- Require a pre-fix baseline and anomaly comparison. If traffic is too low, cap
  evidence at `static_validation` and require a normal pull request.
- Add tamper, replay, incomplete-evidence, serialization, and chain-order tests.
- Update security documentation to match fields actually implemented.

### Exit gate

Changing any recorded input invalidates verification. A causal graph never
claims causality merely because a commit is recent or a model supplied a score.

## Phase 5 — Deployment Correlation and Bounded Repair Loop

Add operational context only after safety and evidence are reliable.

### Requirements

- Normalize commits, pull requests, deployments, Kubernetes rollouts, image
  SHAs, feature flags, and configuration changes into `DeploymentEvent`.
- Correlate error spikes with changes using a sliding window while weighting
  service identity, deployment start, commit SHA, and telemetry proximity.
- Use OpenTelemetry attributes when available without depending on them.
- Support at most 2-3 repair attempts:

  ```text
  hypothesis -> patch -> evaluate -> concrete feedback -> revised patch
  ```

- Hash normalized patch structure and normalized failure output.
- Stop when the same patch/failure pair repeats or failure is materially
  unchanged; route to human review.
- Keep Trust Gate as the final policy boundary.
- Add production cool-off only after baseline and traffic requirements pass.

### Exit gate

Replay tests show deployment correlation improves diagnosis without treating
temporal proximity as causality. Repeated failures stop automatically and
cannot escalate execution privileges.

## Phase 6 — Benchmark, Controlled Rollout, and Product Proof

Prove the product against real tasks and measured alternatives.

### Benchmark requirements

- Do not silently fall back to synthetic fixtures in published SWE-bench runs.
- Fail loudly when the official dataset cannot be loaded.
- Apply generated patches to clean upstream repositories.
- Run both `FAIL_TO_PASS` and `PASS_TO_PASS` tests in isolated environments.
- Report patch, test, timeout, Trust Gate, and infrastructure failures
  separately.
- Publish dataset revision, model, prompts, seed, environment, and exact
  command.
- Keep synthetic fixtures as a separately named offline benchmark.

### Controlled-rollout requirements

- Evaluate at least 100 replayable incidents.
- Compare with a defined baseline, such as a plain coding agent or established
  observability remediation workflow.
- Publish successes and representative failures.
- Measure root-cause accuracy, patch test-pass rate, false positives, repair
  attempts, rollback success, time to reviewable PR, evidence completeness,
  latency, and cost.
- Start with shadow mode, then PR-only, and only later consider guarded apply.

### Exit gate

The official benchmark is reproducible, the 100-incident evaluation supports
the stated claims, and shadow-mode results show acceptable error rates before
any guarded production trial.

## Recommended Tool Stack

| Capability | Use first | ResponseIQ owns |
|---|---|---|
| Logs, traces, metrics | OpenTelemetry | Evidence normalization and scoring |
| Source structure | Tree-sitter + ast-grep | Bounded context ranking |
| Code history | GitHub API + Git | Change correlation |
| Deployments | Kubernetes API + OTel deployment attributes | Timeline and causal links |
| Feature/config events | OpenFeature + provider webhooks | Common `DeploymentEvent` schema |
| Security checks | Semgrep and native tools | Trust Gate decision |
| Validation | Native test/type tools | Evidence collection |
| Isolation | Git worktrees; Dagger when needed | Validation lifecycle |
| Durable workflows | Explicit async Python; Temporal later | Policy and workflow state |
| Integrations | MCP and webhooks | Adapter contracts |

## Success Metrics

The defensible product claim is:

> Every remediation has a traceable cause, independently collected validation
> evidence, a policy decision, a rollback path, and an outcome record.

Track these per release and per model:

- root-cause accuracy;
- patch application and test-pass rate;
- false-positive and false-negative rates;
- repair attempts per incident;
- rollback success;
- time to reviewable PR;
- evidence completeness and level;
- latency and cost;
- percentage of claims linked to independently collected evidence.

## Phase Dependency Map

| Phase | Depends on | Enables |
|---|---|---|
| 0. Baseline | Existing product | Honest claims and comparable measurement |
| 1. Safety | Phase 0 | Trustworthy policy decisions |
| 2. Context | Phase 1 | Source-grounded diagnosis |
| 3. Validation | Phases 1-2 | Safe application-level evidence |
| 4. Proof | Phases 1-3 | Auditable evidence and accurate levels |
| 5. Correlation/loop | Phases 2-4 | Better RCA and bounded iteration |
| 6. Product proof | Phases 0-5 | Controlled rollout and public claims |

No phase may bypass an earlier exit gate because a model reports high
confidence or a deployment is urgent.

Sources: [OpenTelemetry](https://opentelemetry.io/docs/),
[Tree-sitter](https://tree-sitter.github.io/tree-sitter/),
[Semgrep](https://semgrep.dev/docs/), [Dagger](https://dagger.io/), and
[OpenFeature](https://openfeature.dev/).
