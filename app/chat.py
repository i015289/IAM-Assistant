import json
from pathlib import Path
from typing import AsyncIterator

import anthropic

from app.config import settings
from app.mcp_client import MCPClient

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "CLAUDE.md").read_text()
_CLIENT = anthropic.AsyncAnthropic(
    api_key=settings.anthropic_api_key.get_secret_value(),
    base_url=settings.anthropic_base_url,
)


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

            input_buffers: dict[int, dict] = {}

            async with _CLIENT.messages.stream(
                model="claude-opus-4-7",
                max_tokens=8096,
                system=_SYSTEM_PROMPT,
                messages=conversation,
                tools=tools if tools else anthropic.NOT_GIVEN,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_start":
                        if hasattr(event, "content_block") and event.content_block.type == "tool_use":
                            input_buffers[event.index] = {"block": event.content_block, "buf": ""}
                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "type"):
                            if event.delta.type == "text_delta":
                                yield f"data: {json.dumps(event.delta.text)}\n\n"
                            elif event.delta.type == "input_json_delta":
                                if event.index in input_buffers:
                                    input_buffers[event.index]["buf"] += event.delta.partial_json
                    elif event.type == "content_block_stop":
                        if event.index in input_buffers:
                            entry = input_buffers.pop(event.index)
                            try:
                                entry["block"].input = json.loads(entry["buf"] or "{}")
                            except json.JSONDecodeError:
                                entry["block"].input = {}
                            tool_uses.append(entry["block"])

            if not tool_uses:
                break

            conversation.append({
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": t.id, "name": t.name, "input": t.input}
                    for t in tool_uses
                ],
            })

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
