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
2. Ask which kind of work you want: **Recommendation Engine** (full
   insight-discovery), **Default Dashboard** (the standardized onboarding
   dashboard every account gets, built automatically), or **Transcript to
   Insights** (turn a pasted client meeting transcript into chart
   recommendations grounded in that account's real data).

For the **Recommendation Engine** flow, Claude then:

3. Asks which Recruit CRM account (account number) to analyze.
4. Asks which entity you want chart recommendations for — a plain-text
   numbered list built from the entities actually discovered for that
   account, with "All" first and "Do you have anything in mind?" (free-text)
   last.
5. Asks how many chart recommendations you want.
6. Discovers the account's actual data through `mb` (databases, tables,
   fields, existing charts), scoped to your chosen entity/focus.
7. Analyzes it for meaningful, trustworthy business insights.
8. Presents the requested number of ranked recommendations, each with: what
   it shows, why it's useful, what question it answers, what triggered it,
   and what to investigate.
9. On your confirmation, creates the chosen chart(s) in Metabase via `mb
   card create`, verifies them, and hands you back the card reference.

The **Default Dashboard** flow instead just asks for the account number and
runs `scripts/create_default_dashboard.py`, which discovers the account's
data and builds the standard chart set end-to-end.

The **Transcript to Insights** flow asks for the account number and the
pasted transcript, extracts analytics requirements from it, grounds each in
the account's real data, and presents a numbered list of buildable charts
before asking which to create.

See `docs/workflow.md` for all three flows written out in more detail, and
`CLAUDE.md` for the operating instructions Claude itself follows.

## Project structure

```
CLAUDE.md                  Persistent operating instructions for Claude
README.md                  This file
.env.example                Credential placeholders (copy to .env)
.gitignore
config/analysis-config.md  Tunable defaults (ranking weights, thresholds)
prompts/
  discovery.md              Recommendation Engine: map the account's actual data
  analysis.md                Recommendation Engine: find real insights, data-quality gate
  recommendation.md          Recommendation Engine: rank + format recommendations
  chart-generation.md        Recommendation Engine: create + verify charts in Metabase
  transcript-insights.md     Transcript to Insights: transcript -> grounded chart candidates
docs/
  architecture.md            System shape and rationale
  workflow.md                Human-readable walkthrough of all three flows
scripts/
  mb-login.sh                          One-time helper: .env -> mb auth login
  create_default_dashboard.py          Automates the Default Dashboard flow end-to-end
  default_dashboard_template.json      Fixed chart set the Default Dashboard flow replicates
logs/
  history.jsonl              Local-only, git-ignored audit trail (see CLAUDE.md "History log")
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

- No web pages of this project's own — recommendations and explanations are
  delivered as terminal/chat output; the only dashboard/card content that
  exists is what gets created in Metabase itself (Default Dashboard flow,
  or confirmed Recommendation Engine / Transcript to Insights charts).
- Transcript to Insights creates individual cards only — dashboard assembly
  for that flow is future scope, not built yet.
- Chart creation depends on what the installed `mb` CLI version actually
  supports; if a capability isn't available, Claude will say so rather than
  working around it with a different interface.
