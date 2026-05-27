import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


def _make_app():
    from fastapi import FastAPI
    from app.auth import auth_router, get_current_user
    app = FastAPI()
    app.include_router(auth_router)

    @app.get("/protected")
    async def protected(user=__import__('fastapi').Depends(get_current_user)):
        return {"user": user["preferred_username"]}

    return app


def test_login_redirects_to_idp(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "cid")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "csec")
    monkeypatch.setenv("OIDC_DISCOVERY_URL", "https://idp.example.com/.well-known/openid-configuration")
    monkeypatch.setenv("SESSION_SECRET", "testsecret")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    with patch("app.auth.oauth") as mock_oauth:
        from fastapi.responses import RedirectResponse as _RR
        mock_oauth.oidc.authorize_redirect = AsyncMock(
            return_value=_RR(url="https://idp.example.com/auth", status_code=302)
        )
        app = _make_app()
        client = TestClient(app, follow_redirects=False)
        response = client.get("/auth/login")
        assert response.status_code in (302, 307)


def test_protected_route_redirects_unauthenticated(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OIDC_CLIENT_ID", "cid")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "csec")
    monkeypatch.setenv("OIDC_DISCOVERY_URL", "https://idp.example.com/.well-known/openid-configuration")
    monkeypatch.setenv("SESSION_SECRET", "testsecret")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    app = _make_app()
    client = TestClient(app, follow_redirects=False)
    response = client.get("/protected")
    assert response.status_code in (302, 307)
    assert "/auth/login" in response.headers.get("location", "")
