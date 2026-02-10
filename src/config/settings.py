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
    github_token: Optional[SecretStr] = Field(
        default=None, description="GitHub Token for PR creation"
    )
    openai_api_key: Optional[SecretStr] = Field(
        default=None, description="API Key for AI analysis"
    )

    # Observability
    otel_exporter_otlp_endpoint: Optional[str] = None

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    keywords_config_path: Optional[Path] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def get_keywords_config_path(self) -> Path:
        """Return configured path or default to src/config/keywords.json"""
        if self.keywords_config_path:
            return self.keywords_config_path
        return self.base_dir / "src" / "config" / "keywords.json"


settings = Settings()
