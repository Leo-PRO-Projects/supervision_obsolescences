from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, EmailStr, Field, validator


class Settings(BaseSettings):
    app_name: str = "Obsolescence Supervisor"
    api_v1_str: str = "/api/v1"
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = 60 * 24
    backend_cors_origins: List[str] = Field(default_factory=list)

    database_url: str = Field(..., env="DATABASE_URL")

    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_sender: Optional[EmailStr] = Field(None, env="SMTP_SENDER")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")

    teams_webhook_url: Optional[str] = Field(None, env="TEAMS_WEBHOOK_URL")

    alert_threshold_months: int = Field(6, env="ALERT_THRESHOLD_MONTHS")
    alert_warning_months: int = Field(3, env="ALERT_WARNING_MONTHS")
    alert_critical_months: int = Field(1, env="ALERT_CRITICAL_MONTHS")

    scheduler_timezone: str = Field("Europe/Paris", env="SCHEDULER_TIMEZONE")
    scheduler_enabled: bool = Field(True, env="SCHEDULER_ENABLED")

    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("backend_cors_origins", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:  # type: ignore[override]
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()
