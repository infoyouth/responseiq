from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Local LLM fallback
    use_local_llm_fallback: bool = Field(default=True, description="Fall back to local mock LLM when no OpenAI key")

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
