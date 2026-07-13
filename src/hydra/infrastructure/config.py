from functools import lru_cache
from typing import ClassVar

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from hydra.shared.runtime_environment import RuntimeEnvironment


class Settings(BaseSettings):
    ALLOWED_LOG_LEVELS: ClassVar[frozenset[str]] = frozenset(
        {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    )

    app_name: str = "HYDRA"
    app_version: str = "0.1.0"
    environment: RuntimeEnvironment = RuntimeEnvironment.LOCAL
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://placeholder:placeholder@localhost:5432/hydra_local"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HYDRA_",
        extra="ignore",
    )

    @field_validator("app_name", "app_version", "database_url", "redis_url")
    @classmethod
    def validate_non_empty(cls, value: str, info: ValidationInfo) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(f"{info.field_name} must be provided")
        return normalized_value

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value.startswith("/"):
            raise ValueError("api_prefix must start with '/'")
        if normalized_value != "/" and normalized_value.endswith("/"):
            raise ValueError("api_prefix must not end with '/' unless it is exactly '/'")
        return normalized_value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized_value = value.strip().upper()
        if normalized_value not in cls.ALLOWED_LOG_LEVELS:
            raise ValueError("log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return normalized_value


@lru_cache
def get_settings() -> Settings:
    return Settings()
