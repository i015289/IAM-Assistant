# Hai 本地代理 — SSE chunk 边界缺陷

**现象：** 当 Anthropic API 的流式响应里包含一个 `tool_result` 内容块、且该块 body 超过某个较小阈值（实测约 10–20KB，远低于 aiohttp 默认 `readuntil` 缓冲上限 64KB）时，Claude Code 会抛出 `Separator is not found, and chunk exceed the limit` 错误并中断回答。

**触发条件：** 任何使用 MCP / 工具调用、且工具返回非琐碎数据的模型请求。当 MCP 工具返回多行表格数据时**稳定复现**。

**环境信息：**
- Hai 本地代理版本：（2026-06-08 当时运行在 `localhost:6655` 的版本）
- Claude Code：2026-06-08 最新版
- 模型：`claude-sonnet-latest`
- 操作系统：macOS（Darwin 25.5.0）
- `ANTHROPIC_BASE_URL=http://localhost:6655/anthropic/`

**最小复现步骤：**

1. 在 Claude Code 里提出一个需要单次 MCP 工具调用、且工具会返回约 50 行数据的问题，例如：
   > "用 mcp__er6__query_sql 从 USOBT 表取 50 行 OBJECT='B_BUPA_RLT' 的记录，列出所有 NAME 值。"
2. Claude Code 派发工具调用，开始接收来自 Hai 代理的流式响应。
3. 流式响应在中途中断，错误信息为：`Separator is not found, and chunk exceed the limit`。

**用于定位阈值的探针测试：**

| 探针 | 工具返回 body 大小 | 结果 |
|------|-------------------|------|
| 纯文本问答，无工具调用 | 无 | ✅ 正常 |
| 1 次 SQL 查询返回 5 行 | ~1 KB | ✅ 正常 |
| 1 次 SQL 查询返回 50 行 | ~10–20 KB | ❌ 报错（如上） |

**根因推测：** 代理在转发 SSE 流时，未能在大型 `tool_result` 内容块前后保留 `\n\n` 事件分隔符。整个块被作为一个无分隔符的 chunk 下发，导致客户端 `aiohttp.StreamReader.readuntil(b'\\n\\n')` 缓冲区溢出（默认 65536 字节，但实际触发的阈值远低于该值）。

具体可能是：
- (a) 代理把上游单个大 chunk 缓存后整体重发，但没附加分隔符；或
- (b) 代理在非事件边界处对上游流进行了切分，导致分隔符落在 chunk 内部、而非 chunk 之间。

**修复方向：** 确保代理把上游每个 SSE event 单独、完整、以 `\n\n` 结尾的形式下发；不要修改 event body。如果代理内部对 JSON 进行了重新序列化等转换，必须保证转换后**按 event 粒度 flush 并保留分隔符**。

**用户侧临时绕过：**

- 限制 MCP 工具返回结果不超过 ~10 行。
- 用 sub-agent（Explore / general-purpose）先消化大结果，只把摘要返回主会话。
- 临时的数据库查询，优先在 `mcp__er6__query_sql` 调用上显式带 `rows: 5` 或 `rows: 10`。

---

**另见：** [English version / 英文版](./hai-proxy-sse-chunk-bug-en.md)
