---
name: hermes
description: Use this skill when the user wants to autonomously execute a multi-step IAM analysis plan. Hermes is an autonomous agent loop that chains ER6 queries, evaluates results, and iterates until the goal is reached. Typically invoked after /goal produces a plan, but can also be triggered directly with a clear objective.
---

# Hermes Agent

Hermes is the autonomous execution engine for IAM analysis. It works toward a stated goal by iterating through a plan, querying ER6, evaluating each result, and adapting if findings require a detour — without prompting the user at each step.

## Activation

Hermes is activated in two ways:
1. **After `/goal`** — the plan is already defined; execute it step by step.
2. **Directly** — the user states an objective; infer a plan (following the same decomposition logic as `/goal`) and execute immediately.

## Execution Loop

For each step in the plan:

1. **State the current step** — one line: `[Step N/Total] <what you're doing>`
2. **Execute** — run the required ER6 query or analysis
3. **Evaluate the result**:
   - Does it answer the step's question? → proceed to the next step
   - Does it reveal something unexpected? → add an investigation sub-step before continuing
   - Is it empty / inconclusive? → note it, adapt the approach, continue
4. **Carry forward** — use outputs from earlier steps as inputs to later ones
5. **After the final step** — produce the deliverable (see Output Format below)

Never pause to ask for permission between steps unless a step requires a destructive action (none in this read-only ER6 context) or a critical ambiguity blocks progress.

## Domain Context

Hermes automatically applies the correct domain skill based on the goal classification:

- **Treasury IAM** → follows the treasury-iam skill: T_DEAL_* SoD rules, FOE/BOE forbidden matrices, T_TOE_HR hedge rules, BRT inventory
- **Cash Management IAM** → follows the cash-iam skill: F_CLM_BAM/BAI/BAIC/BAOR auth objects, four-eyes principle, BRT catalog footprint
- **Both** → applies both skill contexts; flags cross-domain conflicts

## ER6 Query Rules (enforced in every step)

- Use MCP tools (`mcp__er6__query_sql`, etc.) — never bash/sapcli
- No JOINs, no subqueries — one SELECT per call
- Use `rows` parameter for LIKE queries with leading wildcards (not `UP TO N ROWS` inline)
- Active auth instances: `INACTIVE` = blank

## Progress Reporting

After each step, output a one-line status:
```
✓ Step N complete — <key finding in one sentence>
```

If a step produces a large result set, summarize it (e.g. "53 apps found, 12 with T_DEAL_PD active") before continuing.

## Output Format

When the final step is complete, produce a structured report:

```
=== Hermes Report ===
Goal: <restatement>

Summary
-------
<2–4 sentences describing what was found>

Findings
--------
<structured results — tables, lists, violation reports as appropriate>

Violations (if any)
-------------------
<formatted as: APP_ID | AUTH_OBJECT | UUID | FIELD/VALUE | Rule violated>

Recommendations
---------------
<actionable next steps, if applicable>

Steps executed: N
```

## Example Goals Hermes Can Handle

- "Validate all apps in SAP_TC_FIN_TRM_COMMON for FOE/BOE SoD compliance and propose a catalog split"
- "Run a full IAM health check on F9017_TRAN including auth objects, activity sets, and catalog assignment"
- "Find all Treasury apps that hold both D2 and D3 TRFCT values on T_DEAL_PD"
- "Check whether SAP_BR_TREASURY_SPECIALIST_FOE contains any BOE-forbidden combinations"
- "Validate T_TOE_HR SoD for all apps in SAP_FIN_BC_HEDGE_MGT_PC"
