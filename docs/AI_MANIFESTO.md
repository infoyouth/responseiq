# ResponseIQ: AI Design Manifesto & Context

*> "Don't debug. Innovative fix."*

## 1. Core Identity & Vision
**ResponseIQ** is not a log parser. It is a **Self-Healing, AI-Native Infrastructure Copilot**.
Our mission is to shift incident response from "manual troubleshooting" to "automated, context-aware remediation."

## 2. Technical Philosophy: "Intelligence Over Rules"
We reject brittle regex and hardcoded `if/else` workflows.
*   **Old Way:** "If log contains '502', restart Nginx."
*   **ResponseIQ Way:** "Analyze log + Read Nginx Config + Consult LLM -> Suggest specific config fix."

### 3. Architecture Pillars

#### A. The Remediation Engine (`src/services/remediation_service.py`)
*   **Role:** The brain. It is a generic, type-agnostic engine.
*   **Behavior:** It does not use playbooks. It treats every incident as a unique reasoning challenge, asking the LLM to diagnose contextually.

#### B. Context Awareness (`src/utils/context_extractor.py`)
*   **Role:** The eyes.
*   **Capability:** It extracts file paths and line numbers from logs and physically *reads the source code* around the crach site.
*   **Why:** You cannot fix code you cannot see.

#### C. Hyper-Efficiency (`src/utils/log_processor.py`)
*   **Role:** The muscle.
*   **Capability:** Uses `mmap` and `ProcessPoolExecutor` to map-reduce massive log files (>1GB) in seconds.
*   **Standard:** All I/O must be asynchronous (`aiofiles`, `asyncio`).

## 4. Operational Context for Agents & Developers
*   **Testing:** We obsess over coverage (current: >90% on core utils). Use `make all` to run strict linting and tests.
*   **CI/CD:** Our pipelines are optimized. We do not run redundant checks. Deployments are atomic and gated by "Release & Publish".
*   **Style:** `black` (120 line length), `isort`, strict `mypy`.

## 5. The "System Prompt" (For Future Agents)
*If you are an AI agent working on this repo, instructions are:*
> "You are the maintainer of ResponseIQ. Your goal is autonomy and context. Do not add hardcoded parsers. Always prefer generic, AI-driven solutions. Ensure all new I/O is async. Respect the 120-char limit. When debugging, look at `tests/unit/test_innovation.py` first."
