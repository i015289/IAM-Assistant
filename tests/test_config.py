import os
import pytest


def test_config_loads_all_required_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "client-id")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("OIDC_DISCOVERY_URL", "https://idp.example.com/.well-known/openid-configuration")
    monkeypatch.setenv("SESSION_SECRET", "supersecret")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    # Force reload so monkeypatched env is picked up
    import importlib
    import app.config as cfg
    importlib.reload(cfg)

    assert cfg.settings.anthropic_api_key == "sk-test"
    assert cfg.settings.oidc_client_id == "client-id"
    assert cfg.settings.base_url == "http://localhost:8080"


def test_config_raises_on_missing_required_var(monkeypatch):
    for var in ["ANTHROPIC_API_KEY", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET",
                "OIDC_DISCOVERY_URL", "SESSION_SECRET", "BASE_URL"]:
        monkeypatch.delenv(var, raising=False)

    import importlib
    import app.config as cfg
    with pytest.raises(Exception):
        importlib.reload(cfg)
