# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please DO NOT open a public GitHub issue for security vulnerabilities.**

To report a security vulnerability, email **info.youthinno@gmail.com** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce (including any PoC code or payload)
- Your ResponseIQ version (`responseiq --version`)
- Any relevant log output (redact secrets)

You will receive an acknowledgement within **48 hours** and a resolution timeline within **7 days**.

We follow [Responsible Disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure) — we'll coordinate a CVE and public disclosure once a fix is released.

---

## AI Safety & Data Privacy

ResponseIQ uses LLMs to analyse logs and source code.

- **Data Transmission** — Log snippets and source context are sent to your configured LLM provider (Ollama locally, or OpenAI/other remote). Review your provider's data-use policy before scanning production logs.
- **No Training** — Standard API endpoints are used. Per most providers' policies, API data is not used for model training — verify this with your specific provider agreement.
- **Secrets** — ResponseIQ makes a best-effort attempt to strip secrets from context before sending to an LLM, but **you are responsible** for ensuring your logs do not contain PII or credentials.

## "Self-Healing" Risks

ResponseIQ generates code patches.

- **All AI-generated fixes require human review** before merging. The Trust Gate enforces this by default.
- **No Warranty** — The software is provided "as is". The maintainers are not liable for broken builds, production downtime, or security regressions introduced via AI suggestions.
- **PR-First** — ResponseIQ creates GitHub PRs rather than directly mutating production code. Never approve an auto-generated PR without reviewing the diff.

---

## Dependency Vulnerability Scanning

This project runs `pip-audit` on every CI run (`make lint`). Supply-chain vulnerabilities in dependencies are triaged promptly.

To scan your own install:

```bash
pip-audit
```
