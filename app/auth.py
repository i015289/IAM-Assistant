from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from itsdangerous import URLSafeTimedSerializer, BadSignature
from app.config import settings

auth_router = APIRouter(prefix="/auth")

# Dev mode: skip OIDC when credentials are not configured
_DEV_MODE = settings.oidc_client_id == "your-client-id"

if not _DEV_MODE:
    oauth = OAuth()
    oauth.register(
        name="oidc",
        client_id=settings.oidc_client_id,
        client_secret=settings.oidc_client_secret.get_secret_value(),
        server_metadata_url=settings.oidc_discovery_url,
        client_kwargs={"scope": "openid profile email"},
    )

_signer = URLSafeTimedSerializer(settings.session_secret.get_secret_value())
_COOKIE = "iam_session"
_MAX_AGE = 8 * 3600  # 8 hours
_DEV_USER = {"sub": "ANZEIGER", "preferred_username": "ANZEIGER"}


def _set_session(response: RedirectResponse, data: dict) -> None:
    token = _signer.dumps(data)
    response.set_cookie(
        _COOKIE, token, httponly=True, samesite="lax", max_age=_MAX_AGE
    )


def _get_session(request: Request) -> dict | None:
    token = request.cookies.get(_COOKIE)
    if not token:
        return None
    try:
        return _signer.loads(token, max_age=_MAX_AGE)
    except BadSignature:
        return None


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency — returns session dict or redirects to login."""
    if _DEV_MODE:
        return _DEV_USER
    session = _get_session(request)
    if session is None:
        raise HTTPException(
            status_code=307,
            headers={"location": "/auth/login"},
        )
    return session


@auth_router.get("/login")
async def login(request: Request):
    if _DEV_MODE:
        return RedirectResponse(url="/")
    redirect_uri = f"{settings.base_url}/auth/callback"
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


@auth_router.get("/callback")
async def callback(request: Request):
    if _DEV_MODE:
        return RedirectResponse(url="/")
    token = await oauth.oidc.authorize_access_token(request)
    user_info = token.get("userinfo") or await oauth.oidc.userinfo(token=token)
    response = RedirectResponse(url="/")
    _set_session(response, {
        "sub": user_info["sub"],
        "preferred_username": user_info.get("preferred_username", user_info.get("email", "unknown")),
    })
    return response


@auth_router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login")
    response.delete_cookie(_COOKIE)
    return response
