---
name: goal
description: Use this skill when the user states a high-level IAM analysis objective they want to accomplish. Captures the goal, decomposes it into concrete steps, then hands off to the hermes agent loop to execute autonomously.
---

# Goal Skill

When this skill is activated, do the following:

## Step 1 — Capture and confirm the goal

Restate the user's goal in one clear sentence. If the goal is ambiguous, ask one clarifying question before proceeding.

## Step 2 — Classify the goal domain

Determine which IAM domain(s) are in scope:
- **Treasury IAM** — T_DEAL_* SoD, FOE/BOE catalog split, T_TOE_HR hedge SoD, package CLOUD_FI_TR_IAM
- **Cash Management IAM** — F_CLM_BAM/BAI/BAIC/BAOR auth objects, bank account lifecycle, catalogs SAP_FIN_BC_CM_*
- **Both** — cross-domain analysis

## Step 3 — Decompose into a concrete plan

Break the goal into numbered, actionable steps. Each step must be:
- Specific enough to execute with a single ER6 query or analysis action
- Ordered so earlier steps provide inputs for later ones
- Tagged with the expected output (e.g. "list of app IDs", "violation report", "split proposal")

Present the plan to the user in this format:

```
Goal: <one-sentence restatement>
Domain: <Treasury / Cash / Both>

Plan:
1. [Step description] → expected output: <what this produces>
2. [Step description] → expected output: <what this produces>
...
N. [Final step] → expected output: <final deliverable>
```

## Step 4 — Hand off to hermes

After presenting the plan, say:

> Plan ready. Type `/hermes` to execute autonomously, or tell me which step to start with.

If the user types `/hermes` or says "go", activate the hermes skill with the full plan as context.
