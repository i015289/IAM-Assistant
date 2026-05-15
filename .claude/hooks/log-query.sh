#!/usr/bin/env bash
# Appends each ER6 SQL query + timestamp to .claude/memo/.session-log.md.
# Called by PostToolUse hook; receives tool input JSON on stdin.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_FILE="$REPO_ROOT/.claude/memo/.session-log.md"

# Read tool input JSON from stdin — schema: {"tool_input":{"sql":...,"rows":...}}
INPUT="$(cat)"
SQL="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('sql',''))" 2>/dev/null)"
ROWS="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('rows',''))" 2>/dev/null)"

if [[ -z "$SQL" ]]; then
  exit 0
fi

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# Initialise log file with header if it doesn't exist
if [[ ! -f "$LOG_FILE" ]]; then
  echo "# Session Query Log" > "$LOG_FILE"
  echo "" >> "$LOG_FILE"
fi

{
  echo "## $TIMESTAMP"
  echo '```sql'
  echo "$SQL"
  echo '```'
  [[ -n "$ROWS" ]] && echo "rows limit: $ROWS"
  echo ""
} >> "$LOG_FILE"
