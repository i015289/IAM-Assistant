#!/usr/bin/env bash
# Validates that a memo file being written to .claude/memo/ contains
# the required section headers. Exits non-zero to block the write if
# sections are missing (PreToolUse hook — non-zero exit blocks the action).

# Hook input schema: {"tool_input":{"file_path":...,"content":...}}
INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)"

# Only validate writes to .claude/memo/*.md (but not INDEX.md or .session-log.md)
if [[ "$FILE_PATH" != *"/.claude/memo/"*.md ]]; then
  exit 0
fi

FILENAME="$(basename "$FILE_PATH")"
if [[ "$FILENAME" == "INDEX.md" || "$FILENAME" == ".session-log.md" ]]; then
  exit 0
fi

# Read new file content from tool_input.content
CONTENT="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('content',''))" 2>/dev/null)"

MISSING=()
for SECTION in "## Findings" "## Decisions" "## Work in Progress" "## Known Good Baselines"; do
  if ! echo "$CONTENT" | grep -qF "$SECTION"; then
    MISSING+=("$SECTION")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "memo-validate: missing required sections in $FILENAME:" >&2
  for S in "${MISSING[@]}"; do
    echo "  - $S" >&2
  done
  echo "Add the missing sections before saving." >&2
  exit 1
fi

exit 0
