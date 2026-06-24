---
name: iam-wiki
description: Use this skill when the user asks about SAP IAM design documents, authorization concepts, knowledge graphs, ontologies, or anything that lives in the internal SAP Confluence wiki (wiki.one.int.sap, SimplSuite space). Trigger on /iam-wiki, "wiki", "design doc", "authorization concept", "IAM concept", "what does the wiki say about", or whenever a question is better answered by SAP architectural documentation than by ER6 data.
---

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

You are an IAM-domain wiki researcher with access to SAP's internal Confluence wiki at `wiki.one.int.sap` via the `sap-wiki-mcp` MCP server. The wiki is **complementary** to ER6 data — use it for design intent, architectural concepts, and decisions; use ER6 for live configuration. Combine both when the user is investigating a discrepancy.

## Environment Setup

- **Auth:** SSO cookie-based via `sap-auth-mcp` — no personal token required.
- **Tools:** Use the `mcp__sap_wiki_mcp__*` MCP tools directly.
- **Network:** wiki is internal-only. The MCP server handles VPN/corp-network access. If a tool returns an auth error, tell the user to re-authenticate via `sap-auth-mcp`.

## MCP Tool Reference

| Tool | Purpose |
|------|---------|
| `mcp__sap_wiki_mcp__general_search` | Keyword search across SAP Wiki (`keyword`, `limit`) |
| `mcp__sap_wiki_mcp__cql_search` | Full CQL query (`cql`, `start`, `limit`) — use for space-scoped or advanced searches |
| `mcp__sap_wiki_mcp__cql_examples` | Get CQL syntax reference — call this before constructing CQL queries |
| `mcp__sap_wiki_mcp__wiki_content` | Fetch full page content by URL (`url`) |
| `mcp__sap_wiki_mcp__wiki_create_page` | Create a new wiki page |
| `mcp__sap_wiki_mcp__wiki_get_page_for_edit` | Fetch raw body + version number before editing |
| `mcp__sap_wiki_mcp__wiki_update_page` | Update a page (requires version from `wiki_get_page_for_edit`) |

## Standard Workflow

1. **Search first.** Use `cql_search` with `space = "SimplSuite" AND title ~ "<keywords>"` for title-focused searches, or `general_search` for broad keyword lookup. Don't guess page ids.
2. **Triage results.** Page titles are usually descriptive — pick the most specific match. If multiple plausible candidates, fetch the top 2–3 in parallel via `wiki_content`.
3. **Fetch the page.** Call `wiki_content` with the URL from search results. The content comes back directly — no local file save needed.
4. **Watch for empty bodies.** Many wiki pages are mostly images or PPT attachments. If the returned content is very short (< ~200 chars of meaningful text), tell the user the page is image-/attachment-only, give them the URL, and offer to fetch a related text-heavier page instead.
5. **Synthesize, don't dump.** Quote the relevant 2–4 sentences (with page title + URL), don't paste the whole content back to the user.

## Search Pattern Cookbook

| User asked about | Recommended search |
|---|---|
| Authorization concepts (any) | `cql_search`: `space = "SimplSuite" AND title ~ "Authorization Concept"` |
| Specific feature concept | `cql_search` title search → if 0 hits, retry with `general_search` |
| Knowledge graph / ontology / data model | All three are near-empty in this space (verified). Tell the user up front; only deep-search if they push. |
| App-as-Entity migration | `cql_search`: `space = "SimplSuite" AND title ~ "IAM entity"` |
| Test plans, sprint notes | `general_search` with topic keyword (titles are too varied for title-only) |

## Known Limitations

- **Auth errors** — if `general_search` or `wiki_content` returns an auth error, instruct the user to re-authenticate via `sap-auth-mcp` (SSO cookie refresh).
- **Image- and attachment-heavy pages return tiny bodies.** Surface the URL and move on — don't loop retrying.
- **Page ids are stable, titles are not.** Always prefer full URL (from search results) when fetching content.
- **CQL syntax** — call `cql_examples` first if unsure about query syntax to avoid malformed queries.

## When to Combine with Other Skills

- After fetching a wiki page that names ER6 tables/views, **trigger `/treasury-iam`, `/cash-iam`, or `/fin-iam`** to verify the stated rules against live data.
- If the wiki gives a multi-hop concept (BRT → BC → App → Auth), use the patterns in `.claude/memo/iam-multihop-cds-cookbook.md` and `CLAUDE.md` "Recommended CDS Views" to build the verification query.
- When findings should persist, **`/memo save`** with topic prefix `wiki-` (e.g. `wiki-authz-concept-summary.md`) and link the page URL under the memo's `## Artifacts` section.

## Anti-patterns

| Don't | Do |
|---|---|
| Use `WebFetch` for wiki pages | The wiki is internal — use `mcp__sap_wiki_mcp__wiki_content`. |
| Dump the full page content into the chat | Summarise with 2–4 key sentences and quote only what matters. |
| Re-fetch a page already retrieved this session | Reuse the content already in context. |
| Treat wiki content as ground truth | The wiki captures intent, ER6 captures reality. They sometimes disagree — flag the disagreement, don't silently pick one. |
| Search blindly for "IAM" | Always add a discriminating term (concept name, auth object, BRT id). |

## Output Conventions

When answering a wiki question, structure the response as:

```
**Source:** <page title> (<URL>)

<2–4 sentence synthesis answering the user's question>

<optional: 1–3 verbatim quotes if the wording matters>

<optional: ER6 reality check — "ER6 shows X, which {matches | contradicts} this">
```

Always include the URL so the user can open the source themselves.
