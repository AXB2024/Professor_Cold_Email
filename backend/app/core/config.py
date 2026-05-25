from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Professor Cold Email Backend"
    environment: str = "development"
    log_level: str = "INFO"

    openai_api_key: str = Field(default="")
    openai_model_summary: str = "gpt-4.1-mini"
    openai_model_email: str = "gpt-4.1-mini"
    openai_temperature: float = 0.7

    http_timeout_seconds: float = 20.0
    max_scraped_chars: int = 8000

    email_provider: str = "smtp"  # smtp or gmail_api
    gmail_from_email: str = ""

    gmail_smtp_user: str = ""
    gmail_smtp_app_password: str = ""

    gmail_api_client_id: str = ""
    gmail_api_client_secret: str = ""
    gmail_api_refresh_token: str = ""
    gmail_api_token_uri: str = "https://oauth2.googleapis.com/token"


@lru_cache
def get_settings() -> Settings:
    return Settings()

