import asyncio
import json
import os


class MCPClient:
    """Manages a long-lived MCP server subprocess over stdio."""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None):
        self._command = command
        self._args = args
        self._env = env
        self._proc: asyncio.subprocess.Process | None = None
        self._request_id = 0
        self.tools: list[dict] = []

    async def start(self) -> None:
        """Start the subprocess and perform MCP handshake."""
        merged_env = {**os.environ, **(self._env or {})}
        self._proc = await asyncio.create_subprocess_exec(
            self._command, *self._args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=merged_env,
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


class MCPMultiClient:
    """Aggregates multiple MCPClient instances, merging their tool lists."""

    def __init__(self, clients: dict[str, "MCPClient"]):
        self._clients = clients
        # Map tool name → client for routing call_tool
        self._tool_owner: dict[str, "MCPClient"] = {}
        self.tools: list[dict] = []

    async def start(self) -> None:
        for name, client in self._clients.items():
            try:
                await client.start()
                for tool in client.tools:
                    self._tool_owner[tool["name"]] = client
                self.tools.extend(client.tools)
            except Exception as exc:
                # Non-fatal: log and continue so one bad server doesn't block others
                import logging
                logging.getLogger(__name__).warning("MCP server %r failed to start: %s", name, exc)

    async def call_tool(self, name: str, arguments: dict) -> str:
        client = self._tool_owner.get(name)
        if client is None:
            raise RuntimeError(f"Unknown MCP tool: {name!r}")
        return await client.call_tool(name, arguments)

    async def stop(self) -> None:
        for client in self._clients.values():
            await client.stop()

    def is_alive(self, name: str) -> bool:
        """Return True if the named MCP server process is running."""
        client = self._clients.get(name)
        if client is None:
            return False
        return client._proc is not None and client._proc.returncode is None

    # Expose proc status of primary client for health check in main.py
    @property
    def _proc(self):
        first = next(iter(self._clients.values()), None)
        return first._proc if first else None
