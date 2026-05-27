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
