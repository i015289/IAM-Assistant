#!/usr/bin/env bash
# Validates that a memo file being written to .claude/memo/ contains
# the required section headers. Exits non-zero to block the write if
# sections are missing (PreToolUse hook — non-zero exit blocks the action).
#
# Behaviour by tool:
# - Write: validates the full content (tool_input.content) before writing.
# - Edit:  short-circuits (exit 0). Edit is a partial replace; computing the
#          post-edit document inside bash is fragile (multi-line, escapes,
#          unicode). Memos are validated when first written, and Edit
#          typically modifies a single section without removing headers.
#          If you suspect an Edit removed required sections, run
#          `bash .claude/hooks/validate-memo.sh` against the file manually.

# Hook input schema: {"tool_name":"Write"|"Edit", "tool_input":{"file_path":...,"content":...}}
INPUT="$(cat)"
TOOL_NAME="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)"
FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)"

# Only validate writes to .claude/memo/*.md (but not INDEX.md or .session-log.md)
if [[ "$FILE_PATH" != *"/.claude/memo/"*.md ]]; then
  exit 0
fi

FILENAME="$(basename "$FILE_PATH")"
if [[ "$FILENAME" == "INDEX.md" || "$FILENAME" == ".session-log.md" ]]; then
  exit 0
fi

# Edit is a partial replace — skip section validation for Edit calls.
# (Full validation runs on the next Write, or when reviewing the file.)
if [[ "$TOOL_NAME" == "Edit" ]]; then
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
