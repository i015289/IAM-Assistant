# Hai Local Proxy — SSE chunk-boundary bug

**Symptom:** Claude Code reports `Separator is not found, and chunk exceed the limit` and aborts the response when an Anthropic API streaming response includes a `tool_result` content block whose body exceeds a small threshold (observed at ~10–20KB, well below aiohttp's 64KB default `readuntil` buffer cap).

**Trigger:** Any model call that uses MCP / tool-use with a non-trivial result body. Reproduces consistently when an MCP tool returns a multi-row table.

**Environment:**
- Hai Local Proxy version: (whatever was running on `localhost:6655` on 2026-06-08)
- Claude Code: latest as of 2026-06-08
- Model: `claude-sonnet-latest`
- OS: macOS (Darwin 25.5.0)
- `ANTHROPIC_BASE_URL=http://localhost:6655/anthropic/`

**Reproduction (minimal):**

1. In Claude Code, ask a question that requires one MCP tool call returning ~50 rows of data, e.g.:
   > "Use mcp__er6__query_sql to fetch 50 rows from USOBT where OBJECT='B_BUPA_RLT', list all NAME values."
2. Claude Code dispatches the tool, receives the streaming response from Hai proxy.
3. Mid-stream the response aborts with: `Separator is not found, and chunk exceed the limit`.

**Probe results that pin down the threshold:**

| Probe | Tool result size | Result |
|-------|------------------|--------|
| Plain text question, no tool call | n/a | ✅ works |
| 1 SQL query returning 5 rows | ~1 KB body | ✅ works |
| 1 SQL query returning 50 rows | ~10–20 KB body | ❌ fails with the error above |

**Root-cause hypothesis:** The proxy's SSE forwarding does not preserve the `\n\n` event delimiter when relaying a large `tool_result` content block. The whole block is delivered as a single un-delimited chunk, which causes the client's `aiohttp.StreamReader.readuntil(b'\\n\\n')` to overflow its buffer (default 65536 bytes, but the threshold for triggering this hits well before that).

Either:
- (a) The proxy is buffering the entire upstream chunk and re-emitting it without the delimiter, OR
- (b) The proxy is splitting the upstream stream at a non-event boundary, causing the delimiter to land inside (not between) chunks.

**Fix direction:** Ensure the proxy emits each upstream SSE event terminated by a literal `\n\n`, with no internal modification to the event body. If the proxy uses a non-passthrough transformer (e.g., re-serializing the JSON), make sure the transformer flushes per-event with the delimiter intact.

**Workaround for users in the meantime:**

- Cap MCP tool result sizes to ≤ 10 rows.
- Use sub-agents (Explore / general-purpose) to consume large results internally and return a small summary to the main session.
- For ad-hoc DB queries, prefer `mcp__er6__query_sql` with `rows: 5` or `rows: 10`.

---

**See also:** [中文版 / Chinese version](./hai-proxy-sse-chunk-bug-zh.md)
