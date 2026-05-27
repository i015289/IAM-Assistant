from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_discovery_url: str
    session_secret: str
    base_url: str


settings = Settings()
