"""Rewrite specific keys in a .env file in place.

Usage (CLI, called from install.bat / install.sh):
    python rewrite_env.py <path-to-.env> KEY1=value1 [KEY2=value2 ...]

Library usage:
    from rewrite_env import rewrite
    rewrite(Path(".env"), {"SESSION_SECRET": "abc...", "ANTHROPIC_API_KEY": "sk-..."})

Each KEY must already exist in the file. Lines not matching any KEY are
preserved verbatim, including comments, blank lines, and trailing-newline
state.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping


def rewrite(path: Path, updates: Mapping[str, str]) -> None:
    """Rewrite each `KEY=...` line in `path` according to `updates`.

    Raises KeyError if any key in `updates` is not present in the file.
    """
    text = path.read_text(encoding="utf-8")
    has_trailing_newline = text.endswith("\n")
    lines = text.splitlines()  # discards the trailing newline if present

    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        replaced = False
        for key, value in updates.items():
            prefix = f"{key}="
            if line.startswith(prefix):
                new_lines.append(f"{key}={value}")
                seen.add(key)
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    missing = set(updates.keys()) - seen
    if missing:
        raise KeyError(f"keys not found in {path}: {sorted(missing)}")

    out = "\n".join(new_lines)
    if has_trailing_newline:
        out += "\n"
    path.write_text(out, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: rewrite_env.py <path> KEY1=value1 [KEY2=value2 ...]", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    updates: dict[str, str] = {}
    for arg in sys.argv[2:]:
        if "=" not in arg:
            print(f"error: argument {arg!r} is not KEY=VALUE", file=sys.stderr)
            sys.exit(2)
        key, value = arg.split("=", 1)
        updates[key] = value
    rewrite(path, updates)


if __name__ == "__main__":
    main()
