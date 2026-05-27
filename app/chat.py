import json
from pathlib import Path
from typing import AsyncIterator

import anthropic

from app.config import settings

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "CLAUDE.md").read_text()


async def stream_chat(
    messages: list[dict],
    mcp,
) -> AsyncIterator[str]:
    """Yield SSE-formatted lines from a streaming Anthropic response.

    Handles tool_use blocks by calling mcp.call_tool() and continuing the
    conversation. Yields text chunks as ``data: <chunk>\\n\\n`` and terminates
    with ``data: [DONE]\\n\\n`` or ``data: [ERROR] <msg>\\n\\n``.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())

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

            async with client.messages.stream(
                model="claude-opus-4-7",
                max_tokens=8096,
                system=_SYSTEM_PROMPT,
                messages=conversation,
                tools=tools if tools else anthropic.NOT_GIVEN,
            ) as stream:
                event_iter = stream.__aiter__()
                while True:
                    try:
                        if hasattr(event_iter, "__anext__"):
                            event = await event_iter.__anext__()
                        else:
                            event = next(event_iter)
                    except (StopAsyncIteration, StopIteration):
                        break
                    if event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
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
