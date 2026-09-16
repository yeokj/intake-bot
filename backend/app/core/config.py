import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TIQC Client Intake & Project Scoping Bot"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "anthropic"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"

    # Server Settings
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Load from .env if present
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()