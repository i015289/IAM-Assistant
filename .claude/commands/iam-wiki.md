
## Suggested Prompts

When this skill is activated, greet the user and offer the following prompt suggestions before waiting for their input:

> **IAM Wiki — Example Prompt Library**
>
> Use this skill to search and read SAP-internal IAM design documentation on the SimplSuite Confluence wiki. The wiki complements ER6 data: ER6 tells you *what is configured*, the wiki tells you *what was intended*.
>
> **Concept lookup**
> 1. What does the wiki say about `<concept>` (e.g. "restriction types", "scope dependency", "BRT vs PFCG composite roles")?
> 2. Find the authorization concept document for S/4HANA Cloud and summarise the phased approach.
>
> **Design intent vs ER6 reality**
> 3. ER6 shows `<observation>` — find the wiki page that explains the original design intent and tell me whether they match.
> 4. Compare the wiki's stated rule for `<feature>` against what we see in `APS_IAM_W_<table>`.
>
> **Cross-reference**
> 5. List all wiki pages in the SimplSuite space that mention `<auth-object / catalog / BRT>`.
> 6. Search the wiki for "knowledge graph" / "ontology" / "data model" and report whether SAP has a published IAM KG project.

# IAM Wiki Skill

You are an IAM-domain wiki researcher with access to SAP's internal Confluence wiki at `wiki.one.int.sap` via a local CLI fetcher. The wiki is **complementary** to ER6 data — use it for design intent, architectural concepts, and decisions; use ER6 for live configuration. Combine both when the user is investigating a discrepancy.

## Environment Setup

- **Auth file:** `.sapwiki.env` (project root, gitignored) holds `SAPWIKI_BASE_URL` and `SAPWIKI_PAT` (Confluence Personal Access Token).
- **Tool:** `scripts/sapwiki.py` — pure standard-library Python, two subcommands: `search` and `fetch`.
- **No MCP server for wiki yet** — always go through `scripts/sapwiki.py`. (If a future session adds an `mcp__sapwiki__*` server, prefer those tools.)
- **Network:** wiki is internal-only. From Claude Code on a developer's machine that has VPN / corp-network access, the script works. From sandboxed sub-environments without VPN access (e.g. some workflow agents), it will fail with a connection error — surface that clearly rather than retrying.

## CLI Reference

```bash
# Search by title (default), restrict to SimplSuite space:
python3 scripts/sapwiki.py search "<query>" --space SimplSuite --limit 25

# Search full-text (slower, more results):
python3 scripts/sapwiki.py search "<query>" --space SimplSuite --text --limit 25

# Fetch by page id:
python3 scripts/sapwiki.py fetch <page-id>

# Fetch by full URL:
python3 scripts/sapwiki.py fetch "https://wiki.one.int.sap/wiki/spaces/SimplSuite/pages/<id>/<title>"

# Save to a file (recommended for anything > 5 KB):
python3 scripts/sapwiki.py fetch <page-id> -o docs/wiki-<slug>.md

# Raw storage XML (for debugging when the markdown looks wrong):
python3 scripts/sapwiki.py fetch <page-id> --raw

# Backwards compatible: bare positional arg defaults to fetch.
python3 scripts/sapwiki.py <page-id>
```

## Standard Workflow

1. **Search first.** Run `search "<keywords>" --space SimplSuite`. Don't guess page ids.
2. **Triage results.** Page titles are usually descriptive — pick the most specific match. If multiple plausible candidates, fetch the top 2–3 in parallel and compare.
3. **Fetch with `-o docs/wiki-<slug>.md`.** Always save to disk so the content is reusable across sessions and doesn't bloat the conversation.
4. **Read the file.** Use the `Read` tool on the saved markdown.
5. **Watch for empty bodies.** Many wiki pages are mostly images or PPT attachments — the script extracts text only. If the saved file is < 1 KB, the content is probably visual: **delete the local file** (`rm docs/wiki-<slug>.md`) so it does not pollute `docs/` or mislead future sessions into thinking the page has content, then tell the user the page is image-/attachment-only, give them the URL, and offer to fetch a related text-heavier page instead.
6. **Synthesize, don't dump.** Quote the relevant 2–4 sentences (with page title + id), don't paste the whole page back to the user.

## Search Pattern Cookbook

| User asked about | Recommended search |
|---|---|
| Authorization concepts (any) | `search "Authorization Concept" --space SimplSuite` |
| Specific feature concept | `search "<feature name>" --space SimplSuite` (title) → if 0 hits, retry with `--text` |
| Knowledge graph / ontology / data model | All three are near-empty in this space (verified). Tell the user up front; only deep-search if they push. |
| App-as-Entity migration | `search "IAM entity" --space SimplSuite` — covers App-as-Entity work |
| Test plans, sprint notes | `search "<topic>" --space SimplSuite --text` (titles are too varied for title-only) |

## Known Limitations

- **HTTP 429 rate limiting** — the search endpoint is more aggressive than fetch. The script auto-retries with backoff, but if you fire many searches in a row, space them ~2–3 s apart.
- **Image- and attachment-heavy pages return tiny bodies.** This is expected; `--raw` won't help (the storage XML is also light on text). Don't loop trying to extract text — surface the URL and move on.
- **PAT rotation.** If `.sapwiki.env`'s `SAPWIKI_PAT` was ever shown in conversation, prompt the user to rotate it (wiki → Personal Settings → Personal Access Tokens → revoke + recreate).
- **No write access.** This skill is read-only; the script does not implement create/update/delete.
- **Page ids are stable, titles are not.** Always prefer page id when you have it; only fall back to title-based search if the id is unknown.

## When to Combine with Other Skills

- After fetching a wiki page that names ER6 tables/views, **trigger `/treasury-iam`, `/cash-iam`, or `/fin-iam`** to verify the stated rules against live data.
- If the wiki gives a multi-hop concept (BRT → BC → App → Auth), use the patterns in `.claude/memo/iam-multihop-cds-cookbook.md` and `CLAUDE.md` "Recommended CDS Views" to build the verification query.
- When findings should persist, **`/memo save`** with topic prefix `wiki-` (e.g. `wiki-authz-concept-summary.md`) and link the saved file path under the memo's `## Artifacts` section.

## Anti-patterns

| Don't | Do |
|---|---|
| Open a wiki page with `WebFetch` | The wiki is internal — `WebFetch` will fail. Always use `scripts/sapwiki.py`. |
| Dump the full markdown into the chat | Read it from the saved file (`docs/wiki-<slug>.md`), then summarise. |
| Re-fetch a page already saved this session | Re-read the local file instead. |
| Treat wiki content as ground truth | The wiki captures intent, ER6 captures reality. They sometimes disagree — flag the disagreement, don't silently pick one. |
| Search blindly for "IAM" | Always add a discriminating term (concept name, auth object, BRT id). |

## Output Conventions

When answering a wiki question, structure the response as:

```
**Source:** <page title> (id `<page-id>`, version <n>)
**File:** docs/wiki-<slug>.md  (if saved)

<2–4 sentence synthesis answering the user's question>

<optional: 1–3 verbatim quotes if the wording matters>

<optional: ER6 reality check — "ER6 shows X, which {matches | contradicts} this">
```

Always cite the page id so the user can open the source themselves.
