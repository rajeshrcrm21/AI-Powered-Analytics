# AI-Powered Advanced Analytics Recommendation Engine

A terminal-first workflow — no web UI, no backend, no database of its own —
that uses Claude + the Metabase CLI (`mb`) to analyze a Recruit CRM
customer's actual analytics data and recommend high-value charts/dashboards.

Everything happens by talking to Claude in VS Code. There is nothing to
`npm install` or `run`.

## Prerequisites

- [Metabase CLI](https://github.com/metabase/metabase) (`mb`) installed and
  on your `PATH`. Check with `mb --help`.
- A Metabase API key (or the ability to log in interactively) for the
  Metabase instance that holds this Recruit CRM account's analytics data.

## One-time setup

1. Copy the env template and fill in real values (never commit the result):

   ```bash
   cp .env.example .env
   # edit .env: MB_URL, MB_API_KEY, MB_PROFILE
   ```

2. Log in:

   ```bash
   ./scripts/mb-login.sh
   ```

   This stores your credentials in the `mb` CLI's own profile store (not in
   this repo) under the profile name from `MB_PROFILE` in `.env`.

   Alternatively, log in interactively without touching `.env` at all:

   ```bash
   mb auth login --profile recruitcrm
   ```

3. Check an existing profile before creating a new one:

   ```bash
   mb auth list --json
   ```

   If a working profile already exists on your machine, you can just tell
   Claude its name instead of running the steps above.

## Starting the workflow

Open this folder in VS Code with Claude Code active, and say any of:

- "Start the project"
- "Start analysis"
- "Analyze an account"
- "Recommend charts"
- "Create analytics"

Claude will then:

1. Verify Metabase CLI configuration.
2. Ask which Recruit CRM account (account number) to analyze.
3. Ask which entity you want chart recommendations for — a plain-text
   numbered list built from the entities actually discovered for that
   account, with "All" first and "Do you have anything in mind?" (free-text)
   last.
4. Ask how many chart recommendations you want.
5. Discover the account's actual data through `mb` (databases, tables,
   fields, existing charts), scoped to your chosen entity/focus.
6. Analyze it for meaningful, trustworthy business insights.
7. Present the requested number of ranked recommendations, each with: what it
   shows, why it's useful, what question it answers, what triggered it, and
   what to investigate.
8. On your confirmation, create the chosen chart(s) in Metabase via `mb card
   create`, verify them, and hand you back the card reference.

See `docs/workflow.md` for the same flow written out in more detail, and
`CLAUDE.md` for the operating instructions Claude itself follows.

## Project structure

```
CLAUDE.md                  Persistent operating instructions for Claude
README.md                  This file
.env.example                Credential placeholders (copy to .env)
.gitignore
config/analysis-config.md  Tunable defaults (ranking weights, thresholds)
prompts/
  discovery.md              Stage 1: map the account's actual data
  analysis.md                Stage 2: find real insights, apply data-quality gate
  recommendation.md          Stage 3: rank + format recommendations
  chart-generation.md        Stage 4: create + verify charts in Metabase
docs/
  architecture.md            System shape and rationale
  workflow.md                Human-readable walkthrough
scripts/
  mb-login.sh                 One-time helper: .env -> mb auth login
```

## Security

- `.env` is git-ignored. Only `.env.example` (placeholders) is committed.
- The real API key lives in the `mb` CLI's own profile store, never in this
  repo, never printed by Claude.
- Claude never connects directly to a database, calls the Metabase REST API
  directly, or uses browser automation — every operation goes through `mb`.

## Related Claude Code skills (not used by this workflow today)

This repo's workflow only needs the `metabase-cli` skill (driving `mb` for
discovery/analysis/chart-creation). If Claude Code is installed with the
broader Metabase skill set, the following are also available and may become
relevant if this project's scope ever expands beyond chart recommendations
(e.g. into embedding Metabase content in another app). They are optional —
Claude will only invoke one if the task genuinely calls for it:

- `metabase-database-metadata` — read/edit the YAML Database Metadata Format
  synced from a Metabase instance.
- `metabase-representation-format` — read/edit/validate Metabase
  Representation Format YAML (collections, cards, dashboards, transforms).
- `metabase-semantic-checker` — verify cross-entity and column references in
  a tree of Representation Format YAML files.
- `metabase-embedding-sso-implementation` — add JWT SSO auth for Metabase
  embedding in an app.
- `metabase-react-sdk-setup` — first-time setup of the Metabase React
  embedding SDK.
- `metabase-static-embedding-to-guest-embedding-upgrade`,
  `metabase-full-app-to-modular-embedding-upgrade`,
  `metabase-modular-embedding-to-modular-embedding-sdk-upgrade`,
  `metabase-modular-embedding-version-upgrade` — migrate/upgrade between
  Metabase embedding approaches or SDK versions.
- `metabase-learning` — spaced-repetition study/quiz coach for learning
  Metabase itself.

## Limitations / what's not built here

- No dashboards or web pages — recommendations and explanations are
  delivered as terminal/chat output.
- Chart creation depends on what the installed `mb` CLI version actually
  supports; if a capability isn't available, Claude will say so rather than
  working around it with a different interface.
