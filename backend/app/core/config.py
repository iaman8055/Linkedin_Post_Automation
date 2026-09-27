from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_name: str = "LinkedIn AI Autopilot"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    database_url: str = "postgresql+psycopg://linkedin:linkedin@localhost:5432/linkedin_autopilot"
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    celery_worker_prefetch_multiplier: int = Field(default=1, ge=1, le=16)
    celery_task_soft_time_limit_seconds: int = Field(default=270, ge=10, le=3600)
    celery_task_time_limit_seconds: int = Field(default=300, ge=10, le=3600)
    publishing_max_attempts: int = Field(default=5, ge=1, le=20)
    publishing_retry_base_seconds: int = Field(default=60, ge=10, le=3600)
    publishing_retry_max_seconds: int = Field(default=3600, ge=60, le=86400)
    publishing_stale_claim_minutes: int = Field(default=15, ge=5, le=1440)
    jwt_secret: SecretStr = SecretStr("development-only-change-me")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "linkedin-ai-autopilot"
    jwt_audience: str = "linkedin-ai-autopilot-api"
    jwt_access_token_expire_minutes: int = Field(default=15, gt=0, le=1440)
    refresh_token_expire_days: int = Field(default=30, gt=0, le=365)
    email_verification_token_expire_hours: int = Field(default=24, gt=0, le=168)
    password_reset_token_expire_minutes: int = Field(default=30, gt=0, le=1440)
    linkedin_client_id: str | None = None
    linkedin_client_secret: SecretStr | None = None
    linkedin_redirect_uri: str = "http://localhost:5173/settings/linkedin/callback"
    linkedin_oauth_scopes: list[str] = Field(
        default_factory=lambda: ["openid", "profile", "email", "w_member_social"]
    )
    linkedin_oauth_state_expire_minutes: int = Field(default=10, gt=0, le=30)
    linkedin_token_encryption_key: SecretStr | None = None
    linkedin_api_version: str = Field(default="202609", pattern=r"^\d{6}$")
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_api_key: SecretStr | None = None
    nvidia_api_key: SecretStr | None = None
    ai_request_timeout_seconds: float = Field(default=60.0, gt=0, le=300)
    ai_max_output_tokens: int = Field(default=4000, gt=0, le=100_000)
    openai_base_url: str = "https://api.openai.com/v1"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    research_provider: str | None = None
    research_api_key: SecretStr | None = None
    research_request_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    tavily_base_url: str = "https://api.tavily.com"
    storage_provider: str = "local"
    storage_local_path: str = "./storage"
    storage_max_image_bytes: int = Field(default=10_485_760, gt=0)
    storage_max_video_bytes: int = Field(default=52_428_800, gt=0)
    storage_max_document_bytes: int = Field(default=10_485_760, gt=0)
    storage_bucket: str | None = None
    storage_region: str | None = None
    storage_endpoint: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: SecretStr | None = None
    storage_force_path_style: bool = False

    @model_validator(mode="after")
    def reject_insecure_production_secret(self) -> "Settings":
        insecure_secret = self.jwt_secret.get_secret_value() == "development-only-change-me"
        secret_too_short = len(self.jwt_secret.get_secret_value()) < 32
        if self.app_env == "production" and (insecure_secret or secret_too_short):
            raise ValueError("JWT_SECRET must contain at least 32 characters in production")
        if self.app_env == "production" and self.celery_task_always_eager:
            raise ValueError("CELERY_TASK_ALWAYS_EAGER must be false in production")
        if self.app_env == "production" and self.storage_provider == "local":
            raise ValueError("STORAGE_PROVIDER must use managed object storage in production")
        return self

    @property
    def docs_enabled(self) -> bool:
        return self.app_env != "production"

    @property
    def linkedin_configured(self) -> bool:
        client_secret = (
            self.linkedin_client_secret.get_secret_value()
            if self.linkedin_client_secret is not None
            else ""
        )
        encryption_key = (
            self.linkedin_token_encryption_key.get_secret_value()
            if self.linkedin_token_encryption_key is not None
            else ""
        )
        return bool(self.linkedin_client_id and client_secret and encryption_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
