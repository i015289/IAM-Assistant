from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: SecretStr
    oidc_client_id: str
    oidc_client_secret: SecretStr
    oidc_discovery_url: str
    session_secret: SecretStr
    base_url: str


settings = Settings()
