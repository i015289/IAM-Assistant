import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.auth import auth_router, get_current_user
from app.chat import stream_chat
from app.config import settings
from app.mcp_client import MCPClient, MCPMultiClient

_ROOT = Path(__file__).parent.parent
_mcp: MCPMultiClient | None = None


def _resolve_env(raw: dict[str, str]) -> dict[str, str]:
    """Expand ${VAR} placeholders using os.environ + settings-loaded secrets."""
    subs = {**os.environ}
    if settings.wiki_api_token is not None:
        subs["WIKI_API_TOKEN"] = settings.wiki_api_token.get_secret_value()
    return {k: re.sub(r"\$\{(\w+)\}", lambda m: subs.get(m.group(1), ""), v)
            for k, v in raw.items()}


def _load_mcp_from_config() -> MCPMultiClient:
    config_path = _ROOT / ".mcp.json"
    config = json.loads(config_path.read_text())
    clients: dict[str, MCPClient] = {}
    for name, entry in config.get("mcpServers", {}).items():
        clients[name] = MCPClient(
            command=entry["command"],
            args=entry.get("args", []),
            env=_resolve_env(entry.get("env") or {}),
        )
    return MCPMultiClient(clients)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mcp
    _mcp = _load_mcp_from_config()
    await _mcp.start()
    yield
    await _mcp.stop()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret.get_secret_value(),
    https_only=settings.base_url.startswith("https"),
)
app.include_router(auth_router)
app.mount("/static", StaticFiles(directory=_ROOT / "ui" / "static"), name="static")
_jinja_env = Environment(
    loader=FileSystemLoader(_ROOT / "ui" / "templates"),
    autoescape=True,
    auto_reload=False,
)


def _render(name: str, **ctx) -> HTMLResponse:
    return HTMLResponse(_jinja_env.get_template(name).render(**ctx))


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: dict = Depends(get_current_user)):
    mcp_alive = _mcp is not None and (_mcp._proc is None or _mcp._proc.returncode is None)
    wiki_alive = _mcp is not None and _mcp.is_alive("sap-wiki")
    return _render(
        "index.html",
        username=user["preferred_username"],
        mcp_status="connected" if mcp_alive else "disconnected",
        wiki_status="connected" if wiki_alive else "disconnected",
        llm_model=settings.llm_model,
    )


class ChatRequest(BaseModel):
    messages: list[dict]


@app.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    origin = request.headers.get("origin", "")
    if origin and origin != settings.base_url:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    return StreamingResponse(
        stream_chat(body.messages, _mcp),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
