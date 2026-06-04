from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: SecretStr
    anthropic_base_url: str = "https://api.anthropic.com"
    oidc_client_id: str
    oidc_client_secret: SecretStr
    oidc_discovery_url: str
    session_secret: SecretStr
    base_url: str
    llm_model: str = "claude-opus-4-7"


settings = Settings()
