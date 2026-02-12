# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within ResponseIQ, please send an e-mail to **info.youthinno@gmail.com**. All security vulnerability reports will be promptly addressed.

Please **DO NOT** create public GitHub issues for security vulnerabilities.

## AI Safety & Data Privacy

ResponseIQ utilizes LLMs (Large Language Models) to analyze logs and source code.
- **Data Transmission**: Snippets of your logs and source code are sent to the configured LLM provider (e.g., OpenAI) for analysis.
- **No Training**: We use standard API endpoints. Per most provider policies (e.g., OpenAI Enterprise/API), data sent via API is *not* used to train their models, but you should verify this with your specific provider agreement.
- ** secrets**: ResponseIQ makes a best-effort attempt to not send secrets, but you are responsible for ensuring your logs do not contain sensitive PII or credentials before scanning.

## "Self-Healing" Risks

ResponseIQ suggests code changes ("patches").
- **Review Required**: All AI-generated code must be reviewed by a human.
- **No Warranty**: The software is provided "as is". The maintainers are not responsible for broken builds, production downtime, or security vulnerabilities introduced by AI suggestions.
