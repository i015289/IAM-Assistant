#!/usr/bin/env bash
# Syncs a skill file written to .claude/skills/ into skills/ (with frontmatter)
# and .claude/commands/ (without frontmatter).
# Called by PostToolUse hook; receives {"tool_input":{"file_path":...}} on stdin.

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)"

# Only act on writes to .claude/skills/*.md
if [[ "$FILE_PATH" != *"/.claude/skills/"*.md ]]; then
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "$FILE_PATH")/../.." && pwd)" || exit 1
FILENAME="$(basename "$FILE_PATH")"

SKILLS_DEST="$REPO_ROOT/skills/$FILENAME"
COMMANDS_DEST="$REPO_ROOT/.claude/commands/$FILENAME"

# Sync to skills/ (full copy including frontmatter)
cp "$FILE_PATH" "$SKILLS_DEST"

# Sync to commands/ (strip frontmatter block — lines between first and second ---)
awk '
  /^---$/ && !found_first { found_first=1; next }
  /^---$/ && found_first  { found_first=0; in_front=0; next }
  found_first             { next }
  !found_first            { print }
' "$FILE_PATH" > "$COMMANDS_DEST"

echo "skill-sync: $FILENAME → skills/ and commands/" >&2
