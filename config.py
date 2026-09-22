#!/usr/bin/python
"""Centralized app configuration, loaded from environment variables / .env."""

from typing import List, Optional, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    flask_env: str = "development"

    # JWT auth
    secret_key: str
    jwt_exp_weeks: int = 4

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "wegoride_user"
    db_password: str
    db_name: str = "wego_db"
    db_ssl_ca: Optional[str] = None
    auto_create_tables: bool = True

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_ssl: bool = False

    # CORS
    cors_origins: str = "*"

    # Payments (Chapa) - wired up in the payments phase
    payment_provider: str = "chapa"
    chapa_secret_key: Optional[str] = None
    chapa_webhook_secret: Optional[str] = None

    # Password-reset email delivery
    mail_api_key: Optional[str] = None
    mail_from_address: Optional[str] = None

    # Uploads
    max_content_length_mb: int = 5

    @property
    def cors_origin_list(self) -> Union[str, List[str]]:
        if self.cors_origins.strip() == "*":
            return "*"
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def redis_url(self) -> str:
        scheme = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{scheme}://{auth}{self.redis_host}:{self.redis_port}"


settings = Settings()
