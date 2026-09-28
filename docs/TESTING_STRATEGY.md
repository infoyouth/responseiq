# ResponseIQ Testing and Regression Strategy

## Purpose

ResponseIQ needs to test more than Python correctness. Its highest-risk contract
is:

```text
incident -> diagnosis -> candidate patch -> validation -> policy -> evidence
```

This strategy catches regressions in that contract while keeping normal pull
requests fast. It uses a test pyramid, deterministic fixtures, isolated
candidate execution, and scheduled quality measurement.

This document is an implementation plan. Existing mechanisms are marked
**implemented**; proposed mechanisms are marked **planned**.

## Design Principles

- **Fast feedback first:** most PR checks complete locally in under two minutes.
- **Behavior over coverage:** a passing line is not proof of a correct patch.
- **Hermetic by default:** tests do not depend on network, wall-clock timing,
  developer credentials, or shared mutable databases.
- **Clean candidate environments:** candidate patches run in a fresh worktree or
  disposable container, never in the caller checkout.
- **Fail closed:** unavailable validation is a failure or an explicit downgrade,
  never a pass.
- **Deterministic inputs:** pin fixture repositories, dependency locks, model
  mode, random seeds, and external corpus commits.
- **Evidence on failure:** retain JUnit, coverage, logs, diffs, and sandbox
  metadata whenever a test fails.
- **Targeted expensive testing:** mutation, property, service, and external-corpus
  tests run on schedules or affected areas, not on every small documentation PR.

## What Exists Today

### Implemented

- Unit, API, and E2E tests under `tests/`.
- Parallel pytest execution with `pytest-xdist` and `loadscope`.
- Hermetic before/after sandbox regressions for auth, payment, and inventory in
  [tests/fixtures/test_sandbox_regressions.py](../tests/fixtures/test_sandbox_regressions.py).
- Git worktree patch validation and cleanup tests in
  [tests/unit/test_worktree_service.py](../tests/unit/test_worktree_service.py).
- Performance p95 regression tests in
  [tests/unit/test_performance_gate.py](../tests/unit/test_performance_gate.py).
- Proof integrity and tamper-detection tests.
- Negative regression tests for an applicable-but-wrong patch and static-only
  reproduction evidence.
- Bounded Hypothesis properties for log scrubbing and policy checks.
- Candidate validation checks for pytest, Ruff security rules, and syntax,
  including newly added Python files.
- CI JUnit, coverage, HTML-report, and log artifacts.
- Branch-aware coverage with an 80% repository floor; Codecov is configured
  with a 90% patch-coverage target.
- Weekly and manually-triggered Hypothesis and targeted mutmut workflows.
- Python 3.11/3.12 release-candidate checks, package build, fresh-wheel install,
  CLI smoke tests, and API health smoke tests.
- Ruff, mypy, Ruff security rules, and dependency auditing in CI.

### Not yet implemented or not enforced

- A reusable candidate-patch fixture runner for all incident fixtures.
- Expanded Hypothesis coverage for fingerprints, normalization, evidence
  serialization, and policy boundary properties.
- An initial mutation score baseline and a defined killed-mutant threshold.
- Critical-module-specific branch-coverage floors.
- Testcontainers or Dagger service-level isolation.
- A pinned external incident corpus.
- An official patch-execution benchmark as a CI regression gate.
- Fail-closed handling for every unavailable validation tool and a complete
  evidence record for every validation attempt.

## Test Pyramid

### Layer 1: Fast contract tests

**When:** every local change and every PR.

**Scope:** pure functions, schemas, parsers, policy decisions, scrubbing,
serialization, idempotency, retry fingerprints, and error handling.

**Command:**

```bash
uv run pytest tests/unit tests/routers tests/integrations -q
```

Use parametrization for policy matrices and boundary values. Enable pytest
strictness for unknown markers, invalid configuration, and unexpected xfails.
Use `--import-mode=importlib` where compatible so tests exercise the installed
`src/` layout without accidental path pollution.

### Layer 2: Hermetic incident replay

**When:** every source or test PR; required before merging remediation changes.

**Scope:** the real application path fails before a reviewed patch and succeeds
after it. Each fixture must assert expected cause, changed files, policy result,
and evidence level.

**Command:**

```bash
uv run pytest tests/fixtures/test_sandbox_regressions.py -q
```

Each fixture should eventually have this contract:

```text
incident.json       # log, service, expected cause, evidence expectations
repo/               # pinned miniature repository or worktree
reproduce.py        # fails against the buggy revision
expected.patch      # reviewed reference patch
validate.py         # passes after the patch
expected.json       # cause, files, policy, evidence level
```

The runner must:

1. create a fresh temporary worktree;
2. verify the buggy application path fails for the expected reason;
3. apply the reviewed patch with `git apply --check` first;
4. run focused validation, type checks, and security checks;
5. verify the fixed application path succeeds;
6. verify a deliberately wrong patch fails or downgrades to PR-only;
7. record hashes, command results, and cleanup status; and
8. remove the worktree and all generated artifacts.

### Layer 3: Candidate validation tests

**When:** every change to remediation, Trust Gate, worktrees, proof, or
reproduction services.

**Scope:** candidate patches, pre-fix and post-fix reproduction, rollback,
policy downgrade, retry limits, and evidence generation.

Candidate validation must execute in a disposable sandbox with no host secrets,
no network by default, resource limits, and a hard timeout. A pytest exit code
alone is insufficient: the expected exception or incident signature must be
present and tied to the target code path.

### Layer 4: Service integration tests

**When:** scheduled CI, release candidates, or changes to DB/Redis/queue/API
boundaries.

Use Testcontainers for real Postgres, Redis, and queue behavior where mocks do
not test the contract. Pin image versions. Export container logs and database
state on failure. Do not make external service tests a hidden dependency of the
fast PR suite.

### Layer 5: Property and mutation quality tests

**When:** targeted locally; scheduled CI; before changing parsers, policies,
normalization, scrubbing, or evidence schemas.

The current bounded Hypothesis suite covers log-scrubbing and policy properties.
Expand it to properties such as:

- scrubbing never returns an original secret in the outbound payload;
- incident fingerprints are stable under irrelevant log-line changes;
- normalization is idempotent;
- evidence serialization round-trips without changing hashes;
- policy decisions are monotonic at severity and confidence boundaries;
- retry fingerprints are stable under output formatting changes.

The scheduled job currently targets these high-risk modules:

```text
src/responseiq/services/trust_gate.py
src/responseiq/services/worktree_service.py
src/responseiq/config/policy_config.py
src/responseiq/services/performance_gate.py
```

Mutation scope and focused tests are configured; the first scheduled run will
establish runtime and survivor baselines. Set a killed-mutant threshold only
after reviewing that baseline. Do not claim that line coverage represents test
quality; mutation score is the stronger signal for whether assertions detect
realistic behavior changes.

### Layer 6: External pinned corpus

**When:** scheduled CI and release candidates.

Replay 10-20 real incidents from pinned upstream commits for Flask, FastAPI,
Django, and similar projects. Never pull `main` during a test. Store the source
commit, incident input, expected failure, focused test, and expected outcome.
Treat network or upstream availability errors as infrastructure failures, not
as passing tests.

## Local Developer Workflow

### Fast loop

```bash
uv sync --frozen
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src
uv run pytest -n auto --dist=loadscope -q
```

### Focused remediation loop

```bash
uv run pytest tests/fixtures/test_sandbox_regressions.py -q
uv run pytest tests/unit/test_worktree_service.py tests/unit/test_performance_gate.py -q
uv run pytest tests/unit/test_p2_proof_oriented.py tests/unit/test_integrity_gate.py -q
```

### Full local gate

```bash
make all
```

The local gate must use the same commands and lockfile as CI. A test that only
passes through a developer-installed global tool is not a valid regression
check.

### Optional quality jobs

```bash
# Property tests, when present
uv run pytest -m property -q

# Targeted mutation run (POSIX; same pinned version as scheduled CI)
uv run --with mutmut==3.8.0 mutmut run --max-children 2
uv run --with mutmut==3.8.0 mutmut results

# Branch coverage with the CI floor
uv run pytest --cov=src/responseiq --cov-branch --cov-fail-under=80 --cov-report=term-missing -q
```

## CI Pipeline

Use separate jobs with explicit required status checks.

### Job A: changed-file routing

- Skip unrelated work efficiently, but treat changes to `src`, `tests`,
  `pyproject.toml`, `uv.lock`, workflows, Docker, fixtures, or policy files as
  Python/regression changes.
- Documentation-only changes may skip runtime tests.
- Do not allow a skipped required job to make the aggregate check green.

### Job B: fast PR gate

Run on every relevant PR:

```text
ruff format --check
ruff check
mypy
pytest unit/API/fixture contract tests
hermetic sandbox replay
candidate-worktree tests
package build and fresh-wheel smoke test
```

Use `timeout-minutes`, `fail-fast: false` for matrices, and upload JUnit,
coverage, logs, and fixture evidence with `if: always()`.

### Job C: compatibility matrix

For release candidates and changes affecting packaging or runtime compatibility:

- Python 3.11 and 3.12 are the required supported matrix today.
- Add the minimum supported Python version to the release gate.
- Add OS coverage only where the package or subprocess behavior requires it.
- Test the built wheel in a clean virtual environment, not only the source tree.

This follows the mature-project pattern used by OpenTelemetry and Pydantic:
explicit interpreter matrices, pinned environments, bounded job time, and
artifact transfer between build and test jobs.

### Job D: scheduled quality gate

The weekly/manual workflow currently runs the bounded Hypothesis suite and
targeted mutmut modules. Add these only when their fixtures and infrastructure
are ready:

```text
Testcontainers integration suite
pinned external incident corpus
performance regression suite
```

The normal CI job already enforces the branch-coverage floor. Preserve mutation
results and property-test failures in scheduled job logs. A scheduled job may
inform a maintainer without blocking normal PRs, but release promotion must
require it for affected components.

### Job E: release gate

Before publishing:

1. run the full test suite on the supported Python matrix;
2. run hermetic fixture replay and candidate validation;
3. build distributions once and pass artifacts to later jobs;
4. install and smoke-test the exact wheel;
5. run the pinned external corpus;
6. verify no critical mutation or security gate is skipped; and
7. retain the complete release evidence bundle.

## Coverage and Quality Thresholds

Coverage is a diagnostic, not the primary quality target. CI currently enforces
an 80% repository-wide branch-coverage floor, and Codecov is configured with a
90% patch target. Critical-module-specific branch floors and a mutation-score
floor remain future work; the first scheduled mutation run should establish a
baseline before setting that threshold.

Do not raise global coverage by adding shallow tests. A lower global percentage
with stronger incident replay and mutation results is preferable.

## Flake and Failure Policy

- No silent retries for product tests. Retries are allowed only for known CI
  infrastructure failures and must be reported separately.
- Quarantine a flaky test with an owner, issue, reason, and expiry date.
- Never use broad `xfail` or `skip` to hide a regression.
- Preserve failed test output, environment metadata, random seed, fixture commit,
  patch hash, and sandbox logs.
- A test that cannot determine whether the candidate passed must produce a
  human-review downgrade, not a green result.

## Implementation Status

1. **Implemented:** wrong-patch/static-reproduction negative tests, candidate
  worktree validation, and fail-closed performance behavior when baseline data
  is insufficient.
2. **Implemented:** repository branch-coverage floor, Codecov patch target,
  bounded property tests, and weekly/manual targeted mutation workflow.
3. **Next:** reusable fixture runner, expanded property coverage, critical-module
  coverage and mutation thresholds, then Testcontainers or pinned external
  incidents only where local tests cannot prove the contract.

Do not add Dagger, Temporal, a new agent framework, or a full external corpus
until the fixture runner and evidence contract are stable.

## Research Basis

The design reuses practices observed in mature open-source projects and official
maintainer guidance:

- [pytest integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html):
  `src` layout, installed-package testing, import isolation, and strict mode.
- [GitHub Python Actions guidance](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python):
  explicit Python matrices, JUnit/coverage output, and failure artifacts.
- [OpenTelemetry Python CI](https://github.com/open-telemetry/opentelemetry-python/tree/main/.github/workflows):
  generated environment matrices, pinned dependencies, bounded jobs, and
  explicit compatibility coverage.
- [Pydantic CI](https://github.com/pydantic/pydantic/blob/main/.github/workflows/ci.yml):
  broad OS/interpreter matrices, build-artifact testing, selective full builds,
  and separate type/integration jobs.
- [Hypothesis](https://hypothesis.readthedocs.io/en/latest/): property testing,
  shrinking, and reproducible failing examples.
- [coverage.py branch coverage](https://coverage.readthedocs.io/en/latest/branch.html):
  measuring missing control-flow branches rather than only executed lines.
- [mutmut](https://mutmut.readthedocs.io/en/latest/): targeted mutation scope,
  incremental results, dependency-change invalidation, and killed-mutant quality.

## Success Criteria

The strategy is working when:

- local fast checks are predictable and short;
- PRs catch broken application-path behavior, not only mocked calls;
- unavailable validation cannot produce a false green result;
- critical modules have tested failure branches;
- fixture replay is deterministic across local and CI environments;
- scheduled mutation and property tests find defects ordinary coverage misses;
- release artifacts are tested after installation; and
- every remediation result contains reproducible validation evidence.
