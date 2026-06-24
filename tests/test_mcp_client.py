import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_call_tool_returns_text_result():
    """call_tool sends a tools/call request and returns the text content."""
    from app.mcp_client import MCPClient

    mock_response = json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [{"type": "text", "text": "DEVCLASS|PACKTYPE\nCLOUD_FI_TR_IAM|C"}]
        }
    }) + "\n"

    with patch("app.mcp_client.asyncio.create_subprocess_exec") as mock_exec:
        proc = MagicMock()
        proc.stdout = AsyncMock()
        proc.stdout.readline = AsyncMock(side_effect=[
            # initialize response (id=1)
            (json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "er6-mcp", "version": "0.1.0"}}}) + "\n").encode(),
            # tools/list response (id=2)
            (json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "query_sql", "description": "Run SQL", "inputSchema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}}]}}) + "\n").encode(),
            # tools/call response (id=3)
            mock_response.encode(),
        ])
        proc.stdin = MagicMock()
        proc.stdin.drain = AsyncMock()
        proc.returncode = None
        mock_exec.return_value = proc

        client = MCPClient("conda", ["run", "--no-capture-output", "-n", "sapcli-env", "python", "mcp-server/er6_mcp_server.py"])
        await client.start()
        result = await client.call_tool("query_sql", {"sql": "SELECT DEVCLASS FROM TDEVC UP TO 1 ROWS"})
        assert "DEVCLASS" in result


@pytest.mark.asyncio
async def test_call_tool_raises_on_error_response():
    """call_tool raises RuntimeError when the server returns an error."""
    from app.mcp_client import MCPClient

    error_response = json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "error": {"code": -32600, "message": "Invalid request"}
    }) + "\n"

    with patch("app.mcp_client.asyncio.create_subprocess_exec") as mock_exec:
        proc = MagicMock()
        proc.stdout = AsyncMock()
        proc.stdout.readline = AsyncMock(side_effect=[
            (json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "er6-mcp", "version": "0.1.0"}}}) + "\n").encode(),
            (json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}) + "\n").encode(),
            error_response.encode(),
        ])
        proc.stdin = MagicMock()
        proc.stdin.drain = AsyncMock()
        proc.returncode = None
        mock_exec.return_value = proc

        client = MCPClient("conda", ["run", "--no-capture-output", "-n", "sapcli-env", "python", "mcp-server/er6_mcp_server.py"])
        await client.start()
        with pytest.raises(RuntimeError, match="Invalid request"):
            await client.call_tool("query_sql", {"sql": "SELECT 1"})
