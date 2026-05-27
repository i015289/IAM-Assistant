import importlib
import sys
import pytest
from pydantic import ValidationError


def test_config_loads_all_required_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "client-id")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("OIDC_DISCOVERY_URL", "https://idp.example.com/.well-known/openid-configuration")
    monkeypatch.setenv("SESSION_SECRET", "supersecret")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    sys.modules.pop("app.config", None)
    import app.config as cfg
    importlib.reload(cfg)

    assert cfg.settings.anthropic_api_key.get_secret_value() == "sk-test"
    assert cfg.settings.oidc_client_id == "client-id"
    assert cfg.settings.base_url == "http://localhost:8080"


def test_config_raises_on_missing_required_var(monkeypatch, tmp_path):
    for var in ["ANTHROPIC_API_KEY", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET",
                "OIDC_DISCOVERY_URL", "SESSION_SECRET", "BASE_URL"]:
        monkeypatch.delenv(var, raising=False)
    # Point env_file at a non-existent path so the .env on disk is not loaded
    monkeypatch.setenv("ENV_FILE", str(tmp_path / "nonexistent.env"))

    sys.modules.pop("app.config", None)
    with pytest.raises(ValidationError):
        import app.config as cfg
        from pydantic_settings import BaseSettings, SettingsConfigDict
        from pydantic import SecretStr

        class _Settings(BaseSettings):
            model_config = SettingsConfigDict(env_file=str(tmp_path / "nonexistent.env"))
            anthropic_api_key: SecretStr
            oidc_client_id: str
            oidc_client_secret: SecretStr
            oidc_discovery_url: str
            session_secret: SecretStr
            base_url: str

        _Settings()
