from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    APP_NAME: str = "AgentPulse"
    APP_ENV: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/v1"

    # Security & Auth
    SECRET_KEY: str = "agentpulse-super-secret-dev-key-change-in-production-min-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CREDENTIAL_ENCRYPTION_KEY: str = "gAAAAABl8n_sample_fernet_key_32_bytes_base64_encoded=="
    SSRF_ALLOW_PRIVATE_IPS: bool = True

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://agentpulse:agentpulse_dev_password@localhost:5432/agentpulse"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if not v:
            return "postgresql+asyncpg://agentpulse:agentpulse_dev_password@localhost:5432/agentpulse"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO / S3
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "agentpulse-artifacts"
    S3_REGION: str = "us-east-1"

    # LLM Gateway
    GROQ_API_KEY: str | None = None
    LITELLM_API_BASE: str | None = None
    SIMULATOR_MODEL: str = "groq/openai/gpt-oss-20b"
    GENERATOR_MODEL: str = "groq/openai/gpt-oss-20b"
    JUDGE_MODEL: str = "groq/openai/gpt-oss-20b"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Demo Bot
    DEMO_BOT_URL: str = "http://localhost:8080"


@lru_cache
def get_settings() -> Settings:
    return Settings()
