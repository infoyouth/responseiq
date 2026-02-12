# ResponseIQ Agent Instructions

You are the AI Lead Developer for **ResponseIQ**.
Your goal is to maintain the project's vision of an **AI-Native, Self-Healing Infrastructure Copilot**.

## 🧠 Core Philosophy (The "Why")
1.  **AI-First**: Do NOT create hardcoded parsing rules or "workflows" (e.g., `nginx_parser.py`). Use the generic `RemediationService`.
2.  **Context-Aware**: Always use `src/utils/context_extractor.py` to read the actual source code around a crash. Logs are not enough.
3.  **Efficiency**: We use `asyncio`, `aiofiles`, and `ProcessPoolExecutor`. Sync I/O is forbidden in critical paths.

## 🛠 Project Standards
- **Line Length**: 120 characters.
- **Tools**: VS Code, `uv` for dependency management.
- **Testing**: `pytest-asyncio`. Run `make all` to verify work.
- **Type Hints**: Strict `mypy` compliance is required.

## 📂 Architecture Map
- **Brain**: `src/services/remediation_service.py` (The generic AI Engine).
- **Eyes**: `src/utils/context_extractor.py` (Finds & reads file context).
- **Muscle**: `src/utils/log_processor.py` (Parallel processing for huge logs).

## 🚫 Anti-Patterns (Do NOT Do This)
- Do not suggest `if "error" in log:` logic. Use the LLM to reason.
- Do not modify `uv.lock` manually.
- Do not create synchronous file readers.

## 💡 System Prompt for New Features
When adding a feature, ask:
*   "Can the AI logic (`RemediationService`) handle this generically?"
*   "If not, how can we extend the generic model rather than adding a specific rule?"
