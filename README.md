# ResponseIQ

[![CI](https://github.com/infoyouth/responseiq/actions/workflows/ci.yml/badge.svg)](https://github.com/infoyouth/responseiq/actions)
[![GitHub Release](https://img.shields.io/github/v/release/infoyouth/responseiq)](https://github.com/infoyouth/responseiq/releases)
[![PyPI](https://img.shields.io/pypi/v/responseiq)](https://pypi.org/project/responseiq/)
[![License](https://img.shields.io/github/license/infoyouth/responseiq)](LICENSE)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **"Don't just debug. Fix."**

**ResponseIQ** is an AI-Native **Self-Healing Infrastructure Copilot**.
Unlike traditional parsers that match regex strings, ResponseIQ reads your application logs, **loads your actual source code into an LLM context**, and generates surgical, context-aware remediation patches for incidents.

---

## 📸 See It In Action

![ResponseIQ CLI Demo](docs/assets/demo_placeholder.gif)

*Above: ResponseIQ scanning a crash log, reading the `service.py` file mentioned in the stack trace, and proposing a specific code patch. (Full Asciinema recording coming — see [Try it in 60 seconds](#-try-it-in-60-seconds-no-api-key-needed) to run it yourself.)*

---

## ✨ Key Features

- **🧠 AI-Native Analysis**: Uses Generic AI reasoning instead of fragile regex parsing rules.
- **👁️ Context-Aware**: Reads the local source files referenced in logs to understand *why* the crash happened.
- **⚡ Self-Healing**: Can generate Pull Requests or apply patches directly (CLI mode).
- **🛡️ Battle-Tested**: Includes "Sandbox Mode" to safely test remediation logic.

---

## ⚡ Try it in 60 seconds (no API key needed)

A broken service and a pre-recorded crash log are included in the repo so you can see ResponseIQ work immediately:

```bash
pip install responseiq
git clone https://github.com/infoyouth/responseiq.git && cd responseiq

# Scan the included crash log — no LLM key required
responseiq --mode scan --target ./samples/crash.log
```

Expected output:
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
  3. [HIGH]     ZeroDivisionError: division by zero (reset race)
------------------------------------------------------------
  Tip: run with --mode fix to apply safe remediations.
------------------------------------------------------------
```

See [`samples/README.md`](samples/README.md) for full details on the embedded bugs and how to reproduce them.

---

## 🚀 Quick Start (CLI Tool)

For developers who want to fix bugs in their local environment or CI pipeline.

### 1. Install
```bash
pip install responseiq
```

### 2. Configure an LLM

Choose one option:

**Option A: Ollama (free, fully local — recommended)**
```bash
# Install Ollama: https://ollama.com
ollama serve &
ollama pull llama3.2

# Add to .env in your project root:
echo "LLM_BASE_URL=http://localhost:11434/v1" >> .env
echo "LLM_ANALYSIS_MODEL=llama3.2" >> .env
```

**Option B: OpenAI**
```bash
echo "OPENAI_API_KEY=sk-..." >> .env
```

**Option C: No config (rule-engine fallback)**
Works out of the box with no API key — uses a local heuristic parser.

### 3. Scan Your Logs

```bash
# Use the included sample scenario (fastest path — no setup needed)
responseiq --mode scan --target ./samples/crash.log

# Your own single file (JSON or .log or .txt)
responseiq --mode scan --target ./logs/error.log

# Your own directory
responseiq --mode scan --target ./var/log/app/
```

**Example output:**
```
------------------------------------------------------------
  ResponseIQ Scan Report
  Target : logs/error.log
  Status : SUCCESS
------------------------------------------------------------
  Scanned  : 1 message(s)
  Incidents: 1 found
------------------------------------------------------------
  1. [CRITICAL] Out of Memory Error
     Source     : ai
     Description: The system is experiencing a critical error due to an out of
                  memory condition caused by a resource leak or excessive allocation.
------------------------------------------------------------
  Tip: run with --mode fix to apply safe remediations.
------------------------------------------------------------
```

### 4. Shadow Mode (zero-risk demo)

Analyse all incidents and get a projected MTTR savings report — nothing is changed:
```bash
# Try it on the included samples first
responseiq --mode shadow --target ./samples/ --shadow-report

# Or point at your own logs
responseiq --mode shadow --target ./logs/ --shadow-report
```

---

## 🏢 Platform Server (Self-Hosted)

For Platform Engineers who want a centralized incident response API (webhooks for Datadog, PagerDuty, Sentry etc.).

### Prerequisites
- Docker & Docker Compose
- LLM configured via `.env` (Ollama or OpenAI — see Quick Start above)

### Running with Docker
```bash
# 1. Start the API and Database
docker-compose up -d

# 2. The API is now available at http://localhost:8000
curl http://localhost:8000/health
```

### Development Setup (Local)
We use [UV](https://github.com/astral-sh/uv) for lightning-fast dependency management.

```bash
# Install dependencies
uv sync

# Run the API server with hot-reload
uv run uvicorn src.app:app --reload
```

---

## 🔌 Compatible With

ResponseIQ's webhook API is designed to receive alert payloads from the tools your team already uses. Point your existing alert routing at `POST /api/v1/incidents/ingest` — no agents or plugins required.

| Platform | How to connect |
|---|---|
| **Datadog** | Webhook integration → `POST /api/v1/incidents/ingest` |
| **PagerDuty** | Event Orchestration webhook → same endpoint |
| **Sentry** | Internal Integrations → Webhook URL |
| **GitHub Actions** | `curl` step in your CI workflow (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)) |
| **Alertmanager** | Webhook receiver in `alertmanager.yml` |

> All integrations use standard HTTP webhooks — no vendor-specific SDK required.

---

## 🧪 Development & Contributing

### Workflow
1. **Linting**: `make lint`
2. **Testing**: `make test`
3. **Format**: `make format`

### Project Structure
* `src/cli.py`: Entry point for the CLI tool.
* `src/app.py`: Entry point for the API Server.
* `src/services/remediation_service.py`: The core "Brain" that interfaces with the LLM.

### License
MIT

---

## ⚠️ Disclaimer & Liability

This tool uses **Generative AI** to suggest infrastructure and code fixes.
By using ResponseIQ, you acknowledge that:
1.  **AI Can Hallucinate:** The suggestions provided may be syntactically correct but functionally wrong or insecure.
2.  **Human Review is Mandatory:** You must strictly review all Pull Requests or patches generated by this tool before deploying them.
3.  **No Warranty:** As per the [MIT License](LICENSE), the authors assume **no liability** for system outages, data loss, or security vulnerabilities resulting from the use of this software.

*For security reporting instructions, please see [SECURITY.md](docs/SECURITY.md).*
