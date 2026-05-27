import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


def _make_test_client():
    import importlib
    import app.main as m
    importlib.reload(m)
    return TestClient(m.app)


def test_health_returns_ok(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "cid")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "csec")
    monkeypatch.setenv("OIDC_DISCOVERY_URL", "https://idp.example.com/.well-known/openid-configuration")
    monkeypatch.setenv("SESSION_SECRET", "testsecret")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    with patch("app.main.MCPClient") as mock_mcp_cls:
        mock_mcp_cls.return_value.start = AsyncMock()
        mock_mcp_cls.return_value.tools = []
        client = _make_test_client()
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

    with patch("app.main.MCPClient") as mock_mcp_cls:
        mock_mcp_cls.return_value.start = AsyncMock()
        mock_mcp_cls.return_value.tools = []
        client = _make_test_client()
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (302, 307)
