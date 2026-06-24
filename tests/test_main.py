import importlib
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


def _mock_multi_client():
    mock = MagicMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.tools = []
    mock._proc = None
    return mock


def test_health_returns_ok(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "cid")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "csec")
    monkeypatch.setenv("OIDC_DISCOVERY_URL", "https://idp.example.com/.well-known/openid-configuration")
    monkeypatch.setenv("SESSION_SECRET", "testsecret")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    import app.main as m
    importlib.reload(m)

    with patch.object(m, "_load_mcp_from_config", return_value=_mock_multi_client()):
        with TestClient(m.app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"


def test_root_redirects_unauthenticated(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "cid")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "csec")
    monkeypatch.setenv("OIDC_DISCOVERY_URL", "https://idp.example.com/.well-known/openid-configuration")
    monkeypatch.setenv("SESSION_SECRET", "testsecret")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    import app.main as m
    importlib.reload(m)

    with patch.object(m, "_load_mcp_from_config", return_value=_mock_multi_client()):
        with TestClient(m.app) as client:
            response = client.get("/", follow_redirects=False)
            assert response.status_code in (302, 307)
