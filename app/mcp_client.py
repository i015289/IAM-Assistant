import asyncio
import json
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
        await self._notify("notifications/initialized")

        await self._send({"method": "tools/list", "params": {}})
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

    async def _notify(self, method: str) -> None:
        """Send a JSON-RPC notification (no id, no response expected)."""
        message = {"jsonrpc": "2.0", "method": method}
        line = json.dumps(message) + "\n"
        self._proc.stdin.write(line.encode())
        await self._proc.stdin.drain()

    async def _recv(self) -> dict:
        line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=60.0)
        if not line:
            raise RuntimeError("MCP subprocess closed stdout unexpectedly")
        return json.loads(line.decode().strip())

    async def stop(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            await self._proc.wait()
