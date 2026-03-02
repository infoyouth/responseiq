from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class RepoEntry:
    """
    Maps a service name / package prefix to a source location.

    Fields
    ------
    local_path  : absolute local directory that contains the source tree.
    remote_url  : git remote URL to sparse-checkout when local_path is absent.
    git_ref     : branch, tag, or commit SHA (default: HEAD).
    path_prefix : strip this prefix from stack-trace paths before resolving
                  (useful for monorepo layouts where paths start with
                  e.g. ``services/payments/``).
    service_prefixes : package/module prefixes that identify this repo
                  (e.g. ``["com.example.payments", "payments."]``).
    """

    local_path: Optional[Path] = None
    remote_url: Optional[str] = None
    git_ref: str = "HEAD"
    path_prefix: str = ""
    service_prefixes: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "RepoEntry":
        local = data.get("local_path")
        return cls(
            local_path=Path(local) if local else None,
            remote_url=data.get("remote_url"),
            git_ref=data.get("git_ref", "HEAD"),
            path_prefix=data.get("path_prefix", ""),
            service_prefixes=data.get("service_prefixes", []),
        )


class Settings(BaseSettings):
    # Application Info
    app_name: str = "ResponseIQ MVP"
    environment: str = "dev"  # dev, test, prod

    # Database
    database_url: str = "sqlite:///./responseiq.db"

    # Security / Admin
    blueprint_reload_token: Optional[SecretStr] = None

    # Integrations (Secrets)
    github_token: Optional[SecretStr] = Field(default=None, description="GitHub Token for PR creation")
    openai_api_key: Optional[SecretStr] = Field(default=None, description="API Key for AI analysis")

    # P5.1 Webhook Signing Secrets
    # Set these to verify HMAC-SHA256 signatures on inbound webhooks.
    # Leave unset (None) to skip signature verification (dev/local only).
    datadog_webhook_secret: Optional[SecretStr] = Field(
        default=None, description="Datadog webhook signing secret (X-Datadog-Webhook-Signature)"
    )
    pagerduty_webhook_secret: Optional[SecretStr] = Field(
        default=None, description="PagerDuty v3 webhook signing secret (X-PagerDuty-Signature)"
    )
    sentry_webhook_secret: Optional[SecretStr] = Field(
        default=None, description="Sentry webhook signing secret (sentry-hook-signature)"
    )

    # LLM Model Configuration
    # LLM_ANALYSIS_MODEL — model used for incident analysis + patch synthesis
    llm_analysis_model: str = Field(default="gpt-4o", description="Model for incident analysis and patch synthesis")
    # LLM_FAST_MODEL — cheaper model for detection/classification tasks
    llm_fast_model: str = Field(default="gpt-4o-mini", description="Model for fast detection and classification")
    # LLM_REPRO_MODEL — model for reproduction test generation (needs strong code reasoning)
    llm_repro_model: str = Field(default="gpt-4o", description="Model for reproduction test code generation")
    # LLM_MAX_TOKENS — cap for analysis+patch responses (needs room for multi-line patches)
    llm_max_tokens: int = Field(default=2000, description="Max tokens for analysis/patch LLM responses")
    # LLM_REPRO_MAX_TOKENS — cap for reproduction test code generation
    llm_repro_max_tokens: int = Field(default=1500, description="Max tokens for reproduction test generation")

    # PII / Secret Scrubbing
    # SCRUB_ENABLED — set to false only in fully air-gapped/on-prem deployments
    scrub_enabled: bool = Field(default=True, description="Scrub PII and secrets from log payloads before LLM calls")

    # Multi-Repo Context Resolution (P2.4)
    # RESPONSEIQ_REPO_MAP — JSON dict: { "service_name": { "local_path": "...", ... } }
    # See RepoEntry for the full schema.
    repo_map: Dict[str, RepoEntry] = Field(
        default_factory=dict,
        description="Maps service/repo names to their source locations for multi-repo context resolution.",
    )

    @field_validator("repo_map", mode="before")
    @classmethod
    def _parse_repo_map(cls, v: object) -> Dict[str, RepoEntry]:
        if isinstance(v, dict):
            result: Dict[str, RepoEntry] = {}
            for name, entry in v.items():
                if isinstance(entry, RepoEntry):
                    result[name] = entry
                elif isinstance(entry, dict):
                    result[name] = RepoEntry.from_dict(entry)
                else:
                    raise ValueError(f"repo_map[{name!r}] must be a dict or RepoEntry, got {type(entry)}")
            return result
        if isinstance(v, str):
            # Allow JSON string from env-var
            return cls._parse_repo_map(json.loads(v))
        raise ValueError(f"repo_map must be a dict, got {type(v)}")

    # Local LLM fallback
    use_local_llm_fallback: bool = Field(default=True, description="Fall back to local mock LLM when no OpenAI key")

    # ---------------------------------------------------------------------------
    # ARQ — async durable task queue (requires Redis)
    # ---------------------------------------------------------------------------
    # ARQ_REDIS_URL — Redis DSN.  Leave unset to fall back to FastAPI BackgroundTasks.
    arq_redis_url: Optional[str] = Field(
        default=None,
        description="Redis DSN for ARQ durable task queue (e.g. redis://localhost:6379/0)",
    )

    # ---------------------------------------------------------------------------
    # Langfuse — LLM call tracing + eval flywheel
    # ---------------------------------------------------------------------------
    # Self-hosted at LANGFUSE_HOST for EU data-residency; cloud.langfuse.com by default.
    langfuse_public_key: Optional[str] = Field(default=None, description="Langfuse project public key")
    langfuse_secret_key: Optional[SecretStr] = Field(default=None, description="Langfuse project secret key")
    langfuse_host: Optional[str] = Field(
        default=None, description="Langfuse host URL (default: https://cloud.langfuse.com)"
    )

    # Temporal durable workflows (P-F4) — feature-flagged, disabled by default.
    # Enable only when a Temporal server is running at TEMPORAL_HOST.
    temporal_enabled: bool = Field(default=False, description="Enable Temporal workflow worker")
    temporal_host: str = Field(default="localhost:7233", description="Temporal server gRPC endpoint")
    temporal_namespace: str = Field(default="responseiq", description="Temporal namespace")
    temporal_task_queue: str = Field(default="responseiq-remediation", description="Temporal task queue name")

    # Observability
    otel_exporter_otlp_endpoint: Optional[str] = None

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    keywords_config_path: Optional[Path] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def get_keywords_config_path(self) -> Path:
        """Return configured path or default to package config/keywords.json"""
        if self.keywords_config_path:
            return self.keywords_config_path
        # Use location relative to this settings file, which works in installed package too
        return Path(__file__).parent / "keywords.json"


settings = Settings()
