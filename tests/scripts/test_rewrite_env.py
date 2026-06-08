"""Tests for scripts/rewrite_env.py — rewrites keys in a .env file in place."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make scripts/ importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import rewrite_env  # noqa: E402


def test_rewrites_existing_key(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("FOO=old\nBAR=keep\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"FOO": "new"})

    assert env.read_text(encoding="utf-8") == "FOO=new\nBAR=keep\n"


def test_rewrites_multiple_keys(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\nB=2\nC=3\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"A": "10", "C": "30"})

    assert env.read_text(encoding="utf-8") == "A=10\nB=2\nC=30\n"


def test_leaves_unrelated_lines_untouched(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("# comment\n\nFOO=old\n# trailing\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"FOO": "new"})

    assert env.read_text(encoding="utf-8") == "# comment\n\nFOO=new\n# trailing\n"


def test_value_with_special_chars_is_written_literally(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=placeholder\n", encoding="utf-8")

    rewrite_env.rewrite(env, {"KEY": "abc=def&ghi#jkl"})

    assert env.read_text(encoding="utf-8") == "KEY=abc=def&ghi#jkl\n"


def test_missing_key_raises(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("FOO=old\n", encoding="utf-8")

    with pytest.raises(KeyError, match="MISSING"):
        rewrite_env.rewrite(env, {"MISSING": "x"})


def test_no_trailing_newline_preserved(tmp_path: Path) -> None:
    """If the source file has no trailing newline, output must not add one."""
    env = tmp_path / ".env"
    env.write_text("FOO=old", encoding="utf-8")

    rewrite_env.rewrite(env, {"FOO": "new"})

    assert env.read_text(encoding="utf-8") == "FOO=new"


def test_cli_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`python rewrite_env.py <path> KEY1=val1 KEY2=val2` must work for install.bat."""
    env = tmp_path / ".env"
    env.write_text("A=1\nB=2\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["rewrite_env.py", str(env), "A=10", "B=20"])
    rewrite_env.main()

    assert env.read_text(encoding="utf-8") == "A=10\nB=20\n"


def test_cli_value_with_equals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI must split on the FIRST `=` only, so values may contain `=`."""
    env = tmp_path / ".env"
    env.write_text("URL=old\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["rewrite_env.py", str(env), "URL=https://x.example.com/?a=1&b=2"])
    rewrite_env.main()

    assert env.read_text(encoding="utf-8") == "URL=https://x.example.com/?a=1&b=2\n"
