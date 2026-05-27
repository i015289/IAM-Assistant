import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.auth import auth_router, get_current_user
from app.chat import stream_chat
from app.config import settings
from app.mcp_client import MCPClient

_MCP_SCRIPT = str(Path(__file__).parent.parent / "mcp-server" / "er6_mcp_server.py")
_mcp: MCPClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mcp
    _mcp = MCPClient(_MCP_SCRIPT)
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
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: dict = Depends(get_current_user)):
    mcp_alive = _mcp is not None and (_mcp._proc is None or _mcp._proc.returncode is None)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "username": user["preferred_username"],
            "mcp_status": "connected" if mcp_alive else "disconnected",
        },
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
    if origin and not origin.startswith(settings.base_url):
        return JSONResponse({"error": "forbidden"}, status_code=403)

    return StreamingResponse(
        stream_chat(body.messages, _mcp),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
