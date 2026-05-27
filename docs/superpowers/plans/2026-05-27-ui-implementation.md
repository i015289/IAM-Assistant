# IAM Assistant Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser-based chat+results UI to the IAM Assistant, served by FastAPI, authenticated via corporate OIDC/SSO, deployed on the internal network.

**Architecture:** FastAPI serves static HTML/CSS/JS from `ui/` and exposes a `/chat` SSE endpoint that calls the Anthropic API (claude-opus-4-7) with streaming, executing ER6 MCP tools inline via a managed subprocess. Auth is OIDC authorization code flow using `authlib` with a signed httponly session cookie. Conversation history lives in the browser (`sessionStorage`); the server is stateless beyond the session cookie.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, anthropic SDK, authlib, itsdangerous (session signing), plain HTML/CSS/JS (no build step), marked.js (CDN)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `app/__init__.py` | Create | Package marker |
| `app/config.py` | Create | Load env vars, validate at startup |
| `app/mcp_client.py` | Create | Manage er6_mcp_server.py subprocess, expose `call_tool()` |
| `app/chat.py` | Create | Anthropic streaming loop + tool execution + SSE formatting |
| `app/auth.py` | Create | OIDC login/callback/logout routes + session dependency |
| `app/main.py` | Create | FastAPI app wiring — mount routes, serve UI, `/health` |
| `ui/templates/index.html` | Create | Single-page shell: header, chat panel, results panel |
| `ui/static/style.css` | Create | Layout, theme, message bubbles, tab bar, warning callouts |
| `ui/static/app.js` | Create | SSE fetch loop, tab manager, markdown render, auto-scroll |
| `app/requirements.txt` | Create | FastAPI, uvicorn, anthropic, authlib, itsdangerous, python-dotenv |
| `.env.example` | Create | Document required environment variables |
| `.gitignore` | Modify | Add `.env` and `.superpowers/` if not already present |
| `tests/test_config.py` | Create | Config validation tests |
| `tests/test_mcp_client.py` | Create | MCP client unit tests (subprocess mocked) |
| `tests/test_chat.py` | Create | Chat streaming tests (Anthropic client mocked) |
| `tests/test_auth.py` | Create | Auth routes tests (OIDC flow mocked) |
| `tests/test_main.py` | Create | Integration: health check, auth-guarded routes |

---

## Task 1: Project scaffold and config

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/requirements.txt`
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/__init__.py` (empty) and `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /path/to/iam-assistant
pip install pytest
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Create `app/requirements.txt`**

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
anthropic>=0.28.0
authlib>=1.3.0
itsdangerous>=2.1.2
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r app/requirements.txt
```

Expected: All packages install without error.

- [ ] **Step 5: Create `app/__init__.py`**

```python
```
(empty file)

- [ ] **Step 6: Create `app/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_discovery_url: str
    session_secret: str
    base_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

> Note: `pydantic-settings` raises `ValidationError` on missing required fields — that's what the test catches. Add `pydantic-settings>=2.0.0` to `app/requirements.txt` and reinstall.

- [ ] **Step 7: Update `app/requirements.txt` to add pydantic-settings**

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
anthropic>=0.28.0
authlib>=1.3.0
itsdangerous>=2.1.2
python-dotenv>=1.0.0
httpx>=0.27.0
pydantic-settings>=2.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

```bash
pip install pydantic-settings
```

- [ ] **Step 8: Create `.env.example`**

```
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# OIDC / SSO
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
OIDC_DISCOVERY_URL=https://your-idp.example.com/.well-known/openid-configuration

# Session
SESSION_SECRET=generate-with-python-secrets-token-hex-32

# Deployment
BASE_URL=http://iam-assistant.internal:8080
```

- [ ] **Step 9: Update `.gitignore`**

Open `.gitignore` and ensure these lines are present (add if missing):

```
.env
.superpowers/
```

- [ ] **Step 10: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 2 passed (set env vars in the monkeypatch test; the missing-var test passes because reload without vars raises `ValidationError`).

- [ ] **Step 11: Commit**

```bash
git add app/__init__.py app/config.py app/requirements.txt .env.example .gitignore tests/__init__.py tests/test_config.py
git commit -m "feat: project scaffold and config loading"
```

---

## Task 2: MCP client

**Files:**
- Create: `app/mcp_client.py`
- Create: `tests/test_mcp_client.py`

The MCP client manages a long-lived subprocess running `er6_mcp_server.py` over stdio using the MCP JSON-RPC protocol. It starts the process, sends `initialize` + `tools/list` at startup, and dispatches `tools/call` requests.

- [ ] **Step 1: Write failing MCP client tests**

Create `tests/test_mcp_client.py`:

```python
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_call_tool_returns_text_result():
    """call_tool sends a tools/call request and returns the text content."""
    from app.mcp_client import MCPClient

    mock_response = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [{"type": "text", "text": "DEVCLASS|PACKTYPE\nCLOUD_FI_TR_IAM|C"}]
        }
    }) + "\n"

    with patch("app.mcp_client.asyncio.create_subprocess_exec") as mock_exec:
        proc = AsyncMock()
        proc.stdout = AsyncMock()
        proc.stdout.readline = AsyncMock(side_effect=[
            # initialize response
            (json.dumps({"jsonrpc": "2.0", "id": 0, "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "er6-mcp", "version": "0.1.0"}}}) + "\n").encode(),
            # tools/list response
            (json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "query_sql", "description": "Run SQL", "inputSchema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}}]}}) + "\n").encode(),
            # tools/call response
            mock_response.encode(),
        ])
        proc.stdin = AsyncMock()
        proc.returncode = None
        mock_exec.return_value = proc

        client = MCPClient("mcp-server/er6_mcp_server.py")
        await client.start()
        result = await client.call_tool("query_sql", {"sql": "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"})
        assert "DEVCLASS" in result


@pytest.mark.asyncio
async def test_call_tool_raises_on_error_response():
    """call_tool raises RuntimeError when the server returns an error."""
    from app.mcp_client import MCPClient

    error_response = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32600, "message": "Invalid request"}
    }) + "\n"

    with patch("app.mcp_client.asyncio.create_subprocess_exec") as mock_exec:
        proc = AsyncMock()
        proc.stdout = AsyncMock()
        proc.stdout.readline = AsyncMock(side_effect=[
            (json.dumps({"jsonrpc": "2.0", "id": 0, "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "er6-mcp", "version": "0.1.0"}}}) + "\n").encode(),
            (json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}) + "\n").encode(),
            error_response.encode(),
        ])
        proc.stdin = AsyncMock()
        proc.returncode = None
        mock_exec.return_value = proc

        client = MCPClient("mcp-server/er6_mcp_server.py")
        await client.start()
        with pytest.raises(RuntimeError, match="Invalid request"):
            await client.call_tool("query_sql", {"sql": "SELECT 1"})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_mcp_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.mcp_client'`

- [ ] **Step 3: Create `app/mcp_client.py`**

```python
import asyncio
import json
import os
from pathlib import Path


class MCPClient:
    """Manages a long-lived er6_mcp_server.py subprocess over stdio MCP protocol."""

    def __init__(self, server_script: str):
        self._script = str(Path(server_script).resolve())
        self._proc: asyncio.subprocess.Process | None = None
        self._request_id = 0
        self.tools: list[dict] = []

    async def start(self) -> None:
        """Start the subprocess and perform MCP handshake."""
        self._proc = await asyncio.create_subprocess_exec(
            "conda", "run", "--no-capture-output", "-n", "sapcli-env",
            "python", self._script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await self._send({"method": "initialize", "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "iam-assistant-ui", "version": "0.1.0"},
        }})
        await self._recv()  # initialize response

        response = await self._send({"method": "tools/list", "params": {}})
        list_response = await self._recv()
        self.tools = list_response.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Call an MCP tool and return the text result."""
        if self._proc is None or self._proc.returncode is not None:
            await self.start()

        await self._send({
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        response = await self._recv()

        if "error" in response:
            raise RuntimeError(response["error"]["message"])

        contents = response.get("result", {}).get("content", [])
        return "\n".join(c["text"] for c in contents if c.get("type") == "text")

    async def _send(self, payload: dict) -> dict:
        self._request_id += 1
        message = {"jsonrpc": "2.0", "id": self._request_id, **payload}
        line = json.dumps(message) + "\n"
        self._proc.stdin.write(line.encode())
        await self._proc.stdin.drain()
        return message

    async def _recv(self) -> dict:
        line = await self._proc.stdout.readline()
        return json.loads(line.decode().strip())

    async def stop(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            await self._proc.wait()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_mcp_client.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/mcp_client.py tests/test_mcp_client.py
git commit -m "feat: MCP client subprocess wrapper"
```

---

## Task 3: Chat streaming endpoint

**Files:**
- Create: `app/chat.py`
- Create: `tests/test_chat.py`

`chat.py` receives conversation history, calls the Anthropic API with streaming, executes MCP tools on `tool_use` events, and yields SSE-formatted lines.

- [ ] **Step 1: Write failing chat tests**

Create `tests/test_chat.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_stream_yields_text_chunks():
    """stream_chat yields text chunks from the Anthropic response."""
    from app.chat import stream_chat

    mock_mcp = MagicMock()
    mock_mcp.call_tool = AsyncMock(return_value="result data")
    mock_mcp.tools = []

    # Simulate Anthropic streaming events
    fake_events = [
        MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="Hello ")),
        MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="world")),
        MagicMock(type="message_stop"),
    ]

    mock_stream = AsyncMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)
    mock_stream.__aiter__ = MagicMock(return_value=iter(fake_events))

    mock_client = MagicMock()
    mock_client.messages.stream = MagicMock(return_value=mock_stream)

    with patch("app.chat.anthropic.AsyncAnthropic", return_value=mock_client):
        chunks = []
        async for chunk in stream_chat([{"role": "user", "content": "hi"}], mock_mcp):
            chunks.append(chunk)

    assert any("Hello " in c for c in chunks)
    assert any("world" in c for c in chunks)
    assert chunks[-1] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_stream_executes_tool_use():
    """stream_chat calls mcp.call_tool when a tool_use block is received."""
    from app.chat import stream_chat

    mock_mcp = MagicMock()
    mock_mcp.call_tool = AsyncMock(return_value="DEVCLASS|C\nCLOUD_FI_TR_IAM|C")
    mock_mcp.tools = [{"name": "query_sql", "description": "Run SQL", "inputSchema": {}}]

    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.id = "tu_123"
    tool_use_block.name = "query_sql"
    tool_use_block.input = {"sql": "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"}

    fake_events = [
        MagicMock(type="content_block_start", content_block=tool_use_block),
        MagicMock(type="content_block_stop"),
        MagicMock(type="message_stop"),
    ]

    # After tool result, a second stream call returns text
    text_events = [
        MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="Found 1 package.")),
        MagicMock(type="message_stop"),
    ]

    call_count = 0
    def make_stream(*args, **kwargs):
        nonlocal call_count
        events = fake_events if call_count == 0 else text_events
        call_count += 1
        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=False)
        mock_stream.__aiter__ = MagicMock(return_value=iter(events))
        return mock_stream

    mock_client = MagicMock()
    mock_client.messages.stream = MagicMock(side_effect=make_stream)

    with patch("app.chat.anthropic.AsyncAnthropic", return_value=mock_client):
        chunks = []
        async for chunk in stream_chat([{"role": "user", "content": "list packages"}], mock_mcp):
            chunks.append(chunk)

    mock_mcp.call_tool.assert_called_once_with(
        "query_sql", {"sql": "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"}
    )
    assert any("Found 1 package." in c for c in chunks)


@pytest.mark.asyncio
async def test_stream_yields_error_on_exception():
    """stream_chat yields [ERROR] when the Anthropic call raises."""
    from app.chat import stream_chat

    mock_mcp = MagicMock()
    mock_mcp.tools = []

    mock_stream = AsyncMock()
    mock_stream.__aenter__ = AsyncMock(side_effect=Exception("API unavailable"))

    mock_client = MagicMock()
    mock_client.messages.stream = MagicMock(return_value=mock_stream)

    with patch("app.chat.anthropic.AsyncAnthropic", return_value=mock_client):
        chunks = []
        async for chunk in stream_chat([{"role": "user", "content": "hi"}], mock_mcp):
            chunks.append(chunk)

    assert any("[ERROR]" in c for c in chunks)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_chat.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.chat'`

- [ ] **Step 3: Read CLAUDE.md to get the system prompt path**

The system prompt is the full contents of `CLAUDE.md` at the project root. `chat.py` reads it at startup.

- [ ] **Step 4: Create `app/chat.py`**

```python
import json
from pathlib import Path
from typing import AsyncIterator

import anthropic

from app.config import settings
from app.mcp_client import MCPClient

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "CLAUDE.md").read_text()
_CLIENT = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def stream_chat(
    messages: list[dict],
    mcp: MCPClient,
) -> AsyncIterator[str]:
    """Yield SSE-formatted lines from a streaming Anthropic response.

    Handles tool_use blocks by calling mcp.call_tool() and continuing the
    conversation. Yields text chunks as `data: <chunk>\n\n` and terminates
    with `data: [DONE]\n\n` or `data: [ERROR] <msg>\n\n`.
    """
    tools = [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t["inputSchema"],
        }
        for t in mcp.tools
    ]

    conversation = list(messages)

    try:
        while True:
            tool_uses = []
            current_text = ""

            async with _CLIENT.messages.stream(
                model="claude-opus-4-7",
                max_tokens=8096,
                system=_SYSTEM_PROMPT,
                messages=conversation,
                tools=tools if tools else anthropic.NOT_GIVEN,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            current_text += event.delta.text
                            yield f"data: {json.dumps(event.delta.text)}\n\n"
                    elif event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            tool_uses.append(event.content_block)

            if not tool_uses:
                break

            # Append assistant message with tool_use blocks
            conversation.append({
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": t.id, "name": t.name, "input": t.input}
                    for t in tool_uses
                ],
            })

            # Execute each tool and collect results
            tool_results = []
            for tool_use in tool_uses:
                result = await mcp.call_tool(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                })

            conversation.append({"role": "user", "content": tool_results})

        yield "data: [DONE]\n\n"

    except Exception as exc:
        yield f"data: [ERROR] {str(exc)}\n\n"
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_chat.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add app/chat.py tests/test_chat.py
git commit -m "feat: Anthropic streaming chat with MCP tool execution"
```

---

## Task 4: Auth routes (OIDC)

**Files:**
- Create: `app/auth.py`
- Create: `tests/test_auth.py`

OIDC authorization code flow. Uses `authlib` for the OAuth client. Session stored in a signed cookie via `itsdangerous`.

- [ ] **Step 1: Write failing auth tests**

Create `tests/test_auth.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


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
        mock_oauth.oidc.authorize_redirect = MagicMock(
            return_value=MagicMock(status_code=302, headers={"location": "https://idp.example.com/auth"})
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.auth'`

- [ ] **Step 3: Create `app/auth.py`**

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from itsdangerous import URLSafeTimedSerializer, BadSignature
from app.config import settings

auth_router = APIRouter(prefix="/auth")

oauth = OAuth()
oauth.register(
    name="oidc",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.oidc_discovery_url,
    client_kwargs={"scope": "openid profile email"},
)

_signer = URLSafeTimedSerializer(settings.session_secret)
_COOKIE = "iam_session"
_MAX_AGE = 8 * 3600  # 8 hours


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
    session = _get_session(request)
    if session is None:
        raise __import__('fastapi').HTTPException(
            status_code=307,
            headers={"location": "/auth/login"},
        )
    return session


@auth_router.get("/login")
async def login(request: Request):
    redirect_uri = f"{settings.base_url}/auth/callback"
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


@auth_router.get("/callback")
async def callback(request: Request):
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_auth.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/auth.py tests/test_auth.py
git commit -m "feat: OIDC auth routes with signed session cookie"
```

---

## Task 5: FastAPI app wiring

**Files:**
- Create: `app/main.py`
- Create: `ui/templates/index.html` (placeholder — full HTML in Task 6)
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing main tests**

Create `tests/test_main.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Create placeholder `ui/templates/index.html`**

```bash
mkdir -p ui/templates ui/static
```

Create `ui/templates/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>IAM Assistant</title></head>
<body><p>Loading...</p></body>
</html>
```

- [ ] **Step 4: Create `app/main.py`**

```python
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import auth_router, get_current_user
from app.chat import stream_chat
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
    # CSRF: verify Origin matches BASE_URL
    origin = request.headers.get("origin", "")
    from app.config import settings
    if origin and not origin.startswith(settings.base_url):
        return JSONResponse({"error": "forbidden"}, status_code=403)

    return StreamingResponse(
        stream_chat(body.messages, _mcp),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_main.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add app/main.py ui/templates/index.html ui/static/.gitkeep tests/test_main.py
git commit -m "feat: FastAPI app wiring — routes, health check, chat SSE endpoint"
```

---

## Task 6: HTML template

**Files:**
- Modify: `ui/templates/index.html`

Replace the placeholder with the full two-panel layout. No tests for markup — visual correctness is verified manually in Task 8.

- [ ] **Step 1: Write `ui/templates/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IAM Assistant</title>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>

<header id="header">
  <span class="logo">⚡ IAM Assistant</span>
  <div class="header-right">
    <span id="mcp-indicator" class="indicator {{ 'connected' if mcp_status == 'connected' else 'disconnected' }}">
      ● ER6 {{ mcp_status }}
    </span>
    <span class="username">{{ username }}</span>
    <a href="/auth/logout" class="signout">Sign out</a>
  </div>
</header>

<div id="layout">

  <!-- Left: Chat panel -->
  <div id="chat-panel">
    <div id="messages"></div>
    <div id="input-bar">
      <textarea
        id="input"
        placeholder="Ask about roles, catalogs, SoD…"
        rows="1"
      ></textarea>
      <button id="send-btn" onclick="sendMessage()">Send</button>
    </div>
  </div>

  <!-- Right: Results panel -->
  <div id="results-panel">
    <div id="tab-bar">
      <div class="tab active" id="tab-welcome" data-tab="welcome">Welcome</div>
    </div>
    <div id="tab-content">
      <div class="tab-pane active" id="pane-welcome">
        <div class="welcome">
          <h2>IAM Assistant</h2>
          <p>Ask a question in the chat to get started. Results with tables, findings, and analysis will appear here.</p>
          <p>Examples:</p>
          <ul>
            <li>Show BRT coverage for SAP_BR_TREASURY_SPECIALIST_FOE</li>
            <li>Run a SoD scan on the Treasury FOE catalogs</li>
            <li>Check restriction type coverage for SAP_FIN_BC_TRM_TMPL_PC</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

</div>

<script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add ui/templates/index.html
git commit -m "feat: two-panel HTML template with chat and results layout"
```

---

## Task 7: CSS and JavaScript

**Files:**
- Create: `ui/static/style.css`
- Create: `ui/static/app.js` (replaces .gitkeep)

- [ ] **Step 1: Create `ui/static/style.css`**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #1e1e2e;
  --surface: #181825;
  --border: #313244;
  --text: #cdd6f4;
  --muted: #6c7086;
  --accent: #89b4fa;
  --green: #a6e3a1;
  --red: #f38ba8;
  --amber: #f9e2af;
  --header-h: 48px;
}

html, body { height: 100%; background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; font-size: 14px; }

/* Header */
#header {
  height: var(--header-h);
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; flex-shrink: 0;
}
.logo { font-weight: 600; font-size: 15px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.indicator { font-size: 12px; }
.indicator.connected { color: var(--green); }
.indicator.disconnected { color: var(--red); }
.username { color: var(--accent); font-size: 12px; }
.signout { color: var(--muted); font-size: 12px; text-decoration: none; }
.signout:hover { color: var(--text); }

/* Layout */
#layout {
  display: flex;
  height: calc(100vh - var(--header-h));
  overflow: hidden;
}

/* Chat panel */
#chat-panel {
  width: 42%;
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  background: var(--bg);
}
#messages {
  flex: 1; overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 12px;
}
.msg-user {
  align-self: flex-end;
  background: var(--border);
  border-radius: 12px 12px 2px 12px;
  padding: 10px 14px; max-width: 85%;
}
.msg-ai-wrap { align-self: flex-start; display: flex; gap: 8px; max-width: 90%; }
.ai-avatar {
  width: 26px; height: 26px; background: var(--accent);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: var(--bg); flex-shrink: 0; font-weight: 700;
}
.msg-ai {
  background: var(--surface);
  border-radius: 2px 12px 12px 12px;
  padding: 10px 14px; line-height: 1.5;
}
.msg-error { color: var(--red); font-size: 12px; padding: 6px 0; }
.cursor { display: inline-block; animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.datestamp { font-size: 11px; color: var(--muted); text-align: center; }

#input-bar {
  padding: 12px; border-top: 1px solid var(--border);
  background: var(--surface); display: flex; gap: 8px; align-items: flex-end;
}
#input {
  flex: 1; background: var(--border); border: none; border-radius: 8px;
  padding: 8px 12px; color: var(--text); font-size: 13px;
  resize: none; outline: none; font-family: inherit; line-height: 1.5;
  max-height: 96px; overflow-y: auto;
}
#input::placeholder { color: var(--muted); }
#send-btn {
  background: var(--accent); color: var(--bg); border: none;
  border-radius: 8px; padding: 8px 16px; font-weight: 600;
  cursor: pointer; flex-shrink: 0; font-size: 13px;
}
#send-btn:disabled { opacity: 0.4; cursor: default; }

/* Results panel */
#results-panel {
  flex: 1; background: var(--surface);
  display: flex; flex-direction: column; overflow: hidden;
}
#tab-bar {
  display: flex; border-bottom: 1px solid var(--border);
  background: var(--bg); overflow-x: auto; flex-shrink: 0;
}
.tab {
  padding: 8px 16px; font-size: 12px; color: var(--muted);
  cursor: pointer; white-space: nowrap; border-bottom: 2px solid transparent;
  user-select: none;
}
.tab.active { color: var(--text); border-bottom-color: var(--accent); background: var(--surface); }
.tab:hover:not(.active) { color: var(--text); }
#tab-content { flex: 1; overflow: hidden; position: relative; }
.tab-pane { display: none; height: 100%; overflow-y: auto; padding: 20px; }
.tab-pane.active { display: block; }

/* Markdown rendered content */
.tab-pane h1,.tab-pane h2 { color: var(--text); margin: 0 0 12px; font-size: 15px; }
.tab-pane h3 { color: var(--accent); font-size: 13px; margin: 16px 0 8px; }
.tab-pane p { margin: 0 0 10px; line-height: 1.6; color: var(--text); }
.tab-pane ul,.tab-pane ol { padding-left: 20px; margin: 0 0 10px; }
.tab-pane li { margin: 4px 0; line-height: 1.6; }
.tab-pane code { background: var(--border); padding: 2px 5px; border-radius: 3px; font-size: 12px; }
.tab-pane pre { background: var(--border); padding: 12px; border-radius: 6px; overflow-x: auto; margin: 0 0 12px; }
.tab-pane pre code { background: none; padding: 0; }

/* Tables */
.tab-pane table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 0 0 16px; }
.tab-pane th { text-align: left; padding: 6px 8px; color: var(--accent); font-weight: 600; border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; }
.tab-pane th:hover { color: var(--text); }
.tab-pane td { padding: 6px 8px; border-bottom: 1px solid var(--bg); }
.tab-pane tr:hover td { background: var(--bg); }

/* Warning callout — blockquotes starting with ⚠ */
.tab-pane blockquote {
  border-left: 3px solid var(--amber);
  background: var(--bg); margin: 0 0 12px;
  padding: 10px 14px; border-radius: 0 6px 6px 0;
}
.tab-pane blockquote p { color: var(--amber); margin: 0; font-size: 12px; }

.welcome { max-width: 480px; }
.welcome h2 { font-size: 18px; margin-bottom: 12px; }
.welcome p,.welcome li { color: var(--muted); line-height: 1.7; }
.welcome ul { padding-left: 20px; margin-top: 8px; }
```

- [ ] **Step 2: Create `ui/static/app.js`**

```javascript
// Conversation history stored in sessionStorage
const HISTORY_KEY = 'iam_chat_history';
const MAX_TABS = 10;

let tabCount = 0;

function loadHistory() {
  try { return JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]'); }
  catch { return []; }
}

function saveHistory(messages) {
  sessionStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
}

// Auto-grow textarea up to 4 lines
document.getElementById('input').addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 96) + 'px';
});

// Enter sends, Shift+Enter newline
document.getElementById('input').addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function appendUserMessage(text) {
  const el = document.createElement('div');
  el.className = 'msg-user';
  el.textContent = text;
  document.getElementById('messages').appendChild(el);
  scrollToBottom();
}

function appendAIMessageEl() {
  const wrap = document.createElement('div');
  wrap.className = 'msg-ai-wrap';
  wrap.innerHTML = '<div class="ai-avatar">AI</div><div class="msg-ai"><span class="cursor">▍</span></div>';
  document.getElementById('messages').appendChild(wrap);
  scrollToBottom();
  return wrap.querySelector('.msg-ai');
}

function scrollToBottom() {
  const el = document.getElementById('messages');
  el.scrollTop = el.scrollHeight;
}

function openResultsTab(label) {
  tabCount++;
  const tabId = `tab-${tabCount}`;
  const paneId = `pane-${tabCount}`;

  // Deactivate current tab
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

  // Add new tab
  const tab = document.createElement('div');
  tab.className = 'tab active';
  tab.id = tabId;
  tab.dataset.tab = String(tabCount);
  tab.textContent = label;
  tab.onclick = () => activateTab(tabCount);
  document.getElementById('tab-bar').appendChild(tab);

  // Add new pane
  const pane = document.createElement('div');
  pane.className = 'tab-pane active';
  pane.id = paneId;
  document.getElementById('tab-content').appendChild(pane);

  // Enforce max tabs
  const tabs = document.querySelectorAll('.tab');
  if (tabs.length > MAX_TABS) {
    const oldest = tabs[1]; // tabs[0] is welcome tab
    const oldestNum = oldest.dataset.tab;
    oldest.remove();
    document.getElementById(`pane-${oldestNum}`)?.remove();
  }

  return pane;
}

function activateTab(num) {
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === String(num));
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `pane-${num}`);
  });
}

function enableSortableTable(table) {
  table.querySelectorAll('th').forEach((th, colIdx) => {
    let asc = true;
    th.addEventListener('click', () => {
      const tbody = table.querySelector('tbody');
      if (!tbody) return;
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {
        const aText = a.cells[colIdx]?.textContent.trim() ?? '';
        const bText = b.cells[colIdx]?.textContent.trim() ?? '';
        return asc ? aText.localeCompare(bText) : bText.localeCompare(aText);
      });
      asc = !asc;
      rows.forEach(r => tbody.appendChild(r));
    });
  });
}

function renderMarkdown(pane, raw) {
  pane.innerHTML = marked.parse(raw);
  pane.querySelectorAll('table').forEach(enableSortableTable);
}

function deriveTabLabel(text) {
  // Use first heading found, or first 40 chars of text
  const match = text.match(/^#+\s+(.+)/m);
  if (match) return match[1].slice(0, 40);
  return text.trim().slice(0, 40) || 'Result';
}

async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;

  const sendBtn = document.getElementById('send-btn');
  input.value = '';
  input.style.height = 'auto';
  sendBtn.disabled = true;
  input.disabled = true;

  appendUserMessage(text);

  const history = loadHistory();
  history.push({ role: 'user', content: text });
  saveHistory(history);

  const aiEl = appendAIMessageEl();
  let buffer = '';
  let resultPane = null;

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let partial = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      partial += decoder.decode(value, { stream: true });
      const lines = partial.split('\n');
      partial = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);

        if (payload === '[DONE]') {
          // Finalize
          aiEl.querySelector('.cursor')?.remove();
          const fullText = aiEl.textContent;
          history.push({ role: 'assistant', content: fullText });
          saveHistory(history);

          if (resultPane) renderMarkdown(resultPane, buffer);
          break;
        }

        if (payload.startsWith('[ERROR]')) {
          aiEl.querySelector('.cursor')?.remove();
          const errEl = document.createElement('span');
          errEl.className = 'msg-error';
          errEl.textContent = payload.replace('[ERROR] ', '');
          aiEl.appendChild(errEl);
          break;
        }

        // Normal text chunk (JSON-encoded string)
        let chunk;
        try { chunk = JSON.parse(payload); } catch { chunk = payload; }
        buffer += chunk;

        // Update chat bubble (plain text, no markdown during streaming)
        const cursor = aiEl.querySelector('.cursor');
        const textNode = document.createTextNode(chunk);
        aiEl.insertBefore(textNode, cursor);
        scrollToBottom();

        // Open a results tab on first chunk
        if (resultPane === null) {
          resultPane = openResultsTab('…');
        }
      }
    }

    // Update tab label once we have the full response
    if (resultPane) {
      const label = deriveTabLabel(buffer);
      const activeTab = document.querySelector('.tab.active');
      if (activeTab && activeTab.id !== 'tab-welcome') {
        activeTab.textContent = label;
      }
      renderMarkdown(resultPane, buffer);
    }

  } catch (err) {
    aiEl.querySelector('.cursor')?.remove();
    const errEl = document.createElement('span');
    errEl.className = 'msg-error';
    errEl.textContent = `Error: ${err.message}`;
    aiEl.appendChild(errEl);
  } finally {
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add ui/static/style.css ui/static/app.js
git commit -m "feat: CSS layout and JavaScript chat/streaming/tab logic"
```

---

## Task 8: Manual smoke test

Start the server and verify the UI works end-to-end before calling the feature complete.

- [ ] **Step 1: Create a `.env` file for local testing**

```bash
cp .env.example .env
# Edit .env — fill in real ANTHROPIC_API_KEY and OIDC credentials
# For local testing without a real IDP, you can temporarily bypass auth
# by setting a fake OIDC_DISCOVERY_URL and testing /health first
```

- [ ] **Step 2: Start the server**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Expected output:
```
INFO:     Started server process [...]
INFO:     Application startup complete.
```

- [ ] **Step 3: Verify health check**

```bash
curl http://localhost:8080/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 4: Verify MCP subprocess started**

In the uvicorn logs, confirm no errors about the MCP subprocess. Check:

```bash
curl http://localhost:8080/health
# Should return ok — if MCP failed to start, check .sapcli.env and conda env
```

- [ ] **Step 5: Open the UI in a browser**

Navigate to `http://localhost:8080`. You should be redirected to `/auth/login`, then to the corporate IDP login page.

- [ ] **Step 6: Log in and verify the layout**

After SSO login, confirm:
- Header shows your username and "● ER6 connected"
- Left panel has the chat input
- Right panel shows the Welcome tab with example prompts

- [ ] **Step 7: Send a test message**

Type: `Show me the first 5 packages in TDEVC`

Confirm:
- Message appears in chat, AI response streams in
- A new tab opens in the results panel
- The response renders as a markdown table
- The tab is labelled with the first heading from the response

- [ ] **Step 8: Commit if any fixes were made**

```bash
git add -p  # stage only intentional changes
git commit -m "fix: smoke test corrections"
```

---

## Task 9: Run full test suite

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (≥9 tests across config, mcp_client, chat, auth, main).

- [ ] **Step 2: Fix any failures**

If tests fail, fix root causes. Do not disable tests.

- [ ] **Step 3: Final commit**

```bash
git add -p
git commit -m "chore: passing test suite for IAM Assistant web UI"
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Chat left / results right layout — Task 6, 7
- ✅ FastAPI backend — Task 5
- ✅ OIDC auth — Task 4
- ✅ Anthropic streaming with tool execution — Task 3
- ✅ MCP subprocess client — Task 2
- ✅ Config from env vars — Task 1
- ✅ marked.js markdown rendering — Task 7
- ✅ Sortable table columns — Task 7 (app.js `enableSortableTable`)
- ✅ Warning callouts for ⚠ blockquotes — Task 7 (CSS)
- ✅ Max 10 tabs, oldest dropped — Task 7 (app.js)
- ✅ sessionStorage conversation history — Task 7 (app.js)
- ✅ Streaming cursor indicator — Task 7 (app.js + CSS)
- ✅ Shift+Enter newline, Enter sends — Task 7 (app.js)
- ✅ CSRF Origin check — Task 5 (main.py)
- ✅ .env.example — Task 1
- ✅ .gitignore update — Task 1
- ✅ Deployment instructions — in spec (uvicorn command)
