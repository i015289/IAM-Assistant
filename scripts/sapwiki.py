#!/usr/bin/env python3
"""Fetch a SAP Confluence wiki page and convert to markdown-ish text.

Reads SAPWIKI_BASE_URL and SAPWIKI_PAT from .sapwiki.env (or current env).

Usage:
    # Fetch by page id:
    python scripts/sapwiki.py fetch 1591358514
    # Fetch by URL:
    python scripts/sapwiki.py fetch "https://wiki.one.int.sap/wiki/spaces/SimplSuite/pages/1591358514/Identity+and+Access+Management"
    # Save to a file:
    python scripts/sapwiki.py fetch 1591358514 -o docs/iam-wiki.md
    # Dump raw storage XML (no cleanup):
    python scripts/sapwiki.py fetch 1591358514 --raw
    # Get the full API JSON:
    python scripts/sapwiki.py fetch 1591358514 --json

    # Search for pages by title (CQL):
    python scripts/sapwiki.py search "Authorization Concept"
    # Restrict to a space:
    python scripts/sapwiki.py search "Authorization Concept" --space SimplSuite
    # Full-text search (not just title):
    python scripts/sapwiki.py search "knowledge graph" --text

    # Backwards compatible: bare arg defaults to fetch
    python scripts/sapwiki.py 1591358514
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".sapwiki.env"


def load_env() -> tuple[str, str]:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k.strip(), v)
    base = os.environ.get("SAPWIKI_BASE_URL")
    pat = os.environ.get("SAPWIKI_PAT")
    if not base or not pat:
        sys.exit("error: SAPWIKI_BASE_URL or SAPWIKI_PAT missing (check .sapwiki.env)")
    return base.rstrip("/"), pat


def extract_page_id(arg: str) -> str:
    if arg.isdigit():
        return arg
    m = re.search(r"/pages/(\d+)", arg)
    if m:
        return m.group(1)
    sys.exit(f"error: cannot extract page id from {arg!r}")


def _http_get_json(url: str, pat: str, *, retries: int = 3) -> dict:
    """GET a Confluence JSON endpoint with PAT auth + 429-aware backoff."""
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {pat}", "Accept": "application/json"},
    )
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                # Honour Retry-After if present, else exponential backoff
                ra = e.headers.get("Retry-After") if e.headers else None
                wait = float(ra) if ra and ra.replace(".", "", 1).isdigit() else delay
                print(f"  rate-limited (429), sleeping {wait:.1f}s …", file=sys.stderr)
                time.sleep(wait)
                delay *= 2
                continue
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")[:300]
            except Exception:
                pass
            sys.exit(f"error: HTTP {e.code} from {url}\n{body}")
    sys.exit(f"error: gave up after {retries} retries on {url}")


def fetch_page(base: str, pat: str, page_id: str) -> dict:
    url = f"{base}/wiki/rest/api/content/{page_id}?expand=body.storage,version,space"
    return _http_get_json(url, pat)


def search_pages(base: str, pat: str, query: str, space: str | None, full_text: bool, limit: int) -> list[dict]:
    """Search pages via Confluence CQL.

    By default searches page titles (`title ~ "..."`). With full_text=True,
    searches all text (`text ~ "..."`).
    """
    field = "text" if full_text else "title"
    safe = query.replace('"', '\\"')
    cql_parts = [f'type = "page"', f'{field} ~ "{safe}"']
    if space:
        cql_parts.append(f'space = "{space}"')
    cql = " AND ".join(cql_parts)
    params = urllib.parse.urlencode({"cql": cql, "limit": limit, "expand": "space,version"})
    url = f"{base}/wiki/rest/api/content/search?{params}"
    data = _http_get_json(url, pat)
    return data.get("results", [])


def storage_to_markdown(html: str) -> str:
    """Best-effort Confluence storage XML -> markdown.

    Handles the common subset: headings, lists, tables, links, code blocks,
    and Confluence-specific <ac:link>/<ri:page> tags. Anything weird is
    stripped rather than escaped, since this is for human/LLM reading.
    """
    s = html

    # Confluence internal links: <ac:link><ri:page ri:content-title="X"/>...</ac:link>
    s = re.sub(
        r'<ac:link[^>]*>\s*<ri:page[^>]*ri:content-title="([^"]+)"[^/]*/>\s*(?:<ac:plain-text-link-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-link-body>)?\s*</ac:link>',
        lambda m: f"[[{m.group(2) or m.group(1)}]]",
        s, flags=re.DOTALL,
    )
    # User mentions, attachments, images: drop to a placeholder
    s = re.sub(r"<ac:image[^>]*>.*?</ac:image>", "[image]", s, flags=re.DOTALL)
    s = re.sub(r"<ri:attachment[^/]*/>", "[attachment]", s)
    s = re.sub(r"<ri:user[^/]*/>", "@user", s)

    # Code macros
    s = re.sub(
        r'<ac:structured-macro[^>]*ac:name="code"[^>]*>.*?<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>.*?</ac:structured-macro>',
        lambda m: f"\n```\n{m.group(1)}\n```\n",
        s, flags=re.DOTALL,
    )
    # Info/note/warning panels -> blockquote
    s = re.sub(
        r'<ac:structured-macro[^>]*ac:name="(info|note|warning|tip)"[^>]*>(.*?)</ac:structured-macro>',
        lambda m: f"\n> **{m.group(1).upper()}:** {m.group(2)}\n",
        s, flags=re.DOTALL,
    )
    # Strip remaining ac:/ri: macros
    s = re.sub(r"</?ac:[^>]+>", "", s, flags=re.DOTALL)
    s = re.sub(r"</?ri:[^>]+>", "", s, flags=re.DOTALL)

    # Headings
    for n in range(1, 7):
        s = re.sub(rf"<h{n}[^>]*>(.*?)</h{n}>", lambda m, n=n: f"\n{'#' * n} {m.group(1).strip()}\n", s, flags=re.DOTALL)

    # Tables: produce GFM tables
    def table_repl(m: re.Match) -> str:
        body = m.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body, flags=re.DOTALL)
        out_rows = []
        for r in rows:
            cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, flags=re.DOTALL)
            cells = [re.sub(r"\s+", " ", strip_tags(c)).strip() for c in cells]
            if cells:
                out_rows.append("| " + " | ".join(cells) + " |")
        if not out_rows:
            return ""
        # Insert a separator after the first row to make it a GFM table
        sep = "| " + " | ".join(["---"] * out_rows[0].count("|")) + " |"
        # Fix: count separators correctly
        ncols = out_rows[0].count("|") - 1
        sep = "| " + " | ".join(["---"] * ncols) + " |"
        return "\n" + out_rows[0] + "\n" + sep + "\n" + "\n".join(out_rows[1:]) + "\n"

    s = re.sub(r"<table[^>]*>.*?</table>", table_repl, s, flags=re.DOTALL)

    # Lists
    s = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: f"- {strip_tags(m.group(1)).strip()}\n", s, flags=re.DOTALL)
    s = re.sub(r"</?[uo]l[^>]*>", "\n", s)

    # Links
    s = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', lambda m: f"[{strip_tags(m.group(2)).strip()}]({m.group(1)})", s, flags=re.DOTALL)

    # Paragraphs and breaks
    s = re.sub(r"</p>\s*<p[^>]*>", "\n\n", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</?p[^>]*>", "\n", s)
    s = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", s, flags=re.DOTALL)
    s = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", s, flags=re.DOTALL)

    # Strip any remaining tags
    s = strip_tags(s)
    s = unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def cmd_fetch(args, base: str, pat: str) -> str:
    page_id = extract_page_id(args.page)
    data = fetch_page(base, pat, page_id)
    if args.json:
        return json.dumps(data, indent=2, ensure_ascii=False)
    title = data.get("title", "")
    space = data.get("space", {}).get("key", "")
    version = data.get("version", {}).get("number", "")
    storage = data.get("body", {}).get("storage", {}).get("value", "")
    body = storage if args.raw else storage_to_markdown(storage)
    return f"# {title}\n\n_Space: {space} · Version: {version} · Page id: {page_id}_\n\n{body}"


def cmd_search(args, base: str, pat: str) -> str:
    results = search_pages(base, pat, args.query, args.space, args.text, args.limit)
    if args.json:
        return json.dumps(results, indent=2, ensure_ascii=False)
    if not results:
        return "(no results)\n"
    lines = [f"{len(results)} result(s) for {args.query!r}" + (f" in space {args.space}" if args.space else "") + ":\n"]
    for r in results:
        pid = r.get("id", "?")
        title = r.get("title", "")
        sp = r.get("space", {}).get("key", "")
        lines.append(f"  {pid:>12}  [{sp:<14}]  {title}")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")

    f = sub.add_parser("fetch", help="Fetch a page by id or URL")
    f.add_argument("page", help="Confluence page id or full wiki URL")
    f.add_argument("-o", "--output", help="Write to this file instead of stdout")
    f.add_argument("--raw", action="store_true", help="Output raw storage XML")
    f.add_argument("--json", action="store_true", help="Output the full API JSON response")

    s = sub.add_parser("search", help="Search pages via Confluence CQL")
    s.add_argument("query", help="Search string (matched against title by default)")
    s.add_argument("--space", help="Restrict to this space key (e.g. SimplSuite)")
    s.add_argument("--text", action="store_true", help="Search full text instead of title only")
    s.add_argument("--limit", type=int, default=25, help="Max results (default 25)")
    s.add_argument("-o", "--output", help="Write to this file instead of stdout")
    s.add_argument("--json", action="store_true", help="Output raw API JSON")

    # Backwards compatibility: a bare positional arg defaults to "fetch"
    argv = sys.argv[1:]
    if argv and argv[0] not in {"fetch", "search", "-h", "--help"}:
        argv = ["fetch", *argv]
    args = p.parse_args(argv)

    if not args.cmd:
        p.print_help()
        return 2

    base, pat = load_env()
    if args.cmd == "fetch":
        out = cmd_fetch(args, base, pat)
    else:
        out = cmd_search(args, base, pat)

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"wrote {len(out):,} chars to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
