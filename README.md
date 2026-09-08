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
- "Create analytics"

Claude will then:

1. Verify Metabase CLI configuration.
2. Ask which kind of work you want: **Requirements Intake** (you state chart
   requirements directly — a list, a pasted client doc — and Claude grounds
   each in that account's real data; this project's primary flow), or
   **Transcript to Insights** (turn a pasted client meeting transcript into
   chart recommendations grounded in that account's real data).

The **Requirements Intake** flow asks for the account number and your chart
requirements directly, checks known patterns/reference material first and
falls back to live discovery, asks a clarifying question only when a
requirement is genuinely ambiguous, and presents a numbered list of
buildable charts before asking which to create.

The **Transcript to Insights** flow asks for the account number and the
pasted transcript, extracts analytics requirements from it, grounds each in
the account's real data, and presents a numbered list of buildable charts
before asking which to create.

Every discovery/resolution step in both flows works from schema metadata
(table/column names, types) only — it never samples, queries, or displays
the account's actual row data. The one narrow, documented exception is
described in "Where charts touch real data" below.

See `docs/workflow.md` for both flows written out in more detail, and
`CLAUDE.md` for the operating instructions Claude itself follows.

## Project structure

```
CLAUDE.md                  Persistent operating instructions for Claude
README.md                  This file
.env.example                Credential placeholders (copy to .env)
.gitignore
config/analysis-config.md  Tunable defaults (data-quality thresholds, chart-type defaults)
prompts/
  discovery.md              Map the account's actual data (metadata only, both flows)
  chart-generation.md        Create + verify charts in Metabase (both flows)
  transcript-insights.md     Transcript to Insights: transcript -> grounded chart candidates
  requirements-intake.md     Requirements Intake: stated requirements -> grounded chart candidates
  infeasible-requirement.md  How to handle a requirement the account's real data can't support
  metabase_skill_improvement.md  Prompt for building references/ (schema map, metric glossary,
                              canonical patterns) that Requirements Intake checks first once built
docs/
  architecture.md            System shape and rationale
  workflow.md                Human-readable walkthrough of both flows
references/
  schema-map.md              Structural (metadata-only) map of the 12 core Recruit CRM tables
  metric-glossary.md         Business-term definitions confirmed by the user, per account
scripts/
  mb-login.sh                          One-time helper: .env -> mb auth login
logs/
  history.jsonl              Local-only, git-ignored audit trail (see CLAUDE.md "History log")
```

## Security

- `.env` is git-ignored. Only `.env.example` (placeholders) is committed.
- The real API key lives in the `mb` CLI's own profile store, never in this
  repo, never printed by Claude.
- Claude never connects directly to a database, calls the Metabase REST API
  directly, or uses browser automation — every operation goes through `mb`.

### Where charts touch real data

Discovery, requirement resolution, and follow-up clarifying questions are
metadata-only (table/column names and types via `mb table fields`, existing
card/dashboard *names* via `mb search`) — never a value sample, `SELECT`, or
opened saved query. Business-term definitions (a stage list, what "active"
means) are resolved by asking the user or from `references/metric-glossary.md`,
never by querying live data to check or guess. The one narrow exception:
when a chart genuinely needs native SQL (MBQL can't express the logic), the
finished, user-confirmed query is run once against real data immediately
before saving, because a dry-run can't validate SQL text — see
`prompts/chart-generation.md`'s validation step. MBQL queries only ever get
dry-run validated (never executed) before creation.

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
  exists is what gets created in Metabase itself (confirmed Requirements
  Intake / Transcript to Insights charts).
- Neither flow assembles a dashboard — both create individual cards only;
  dashboard assembly is future scope, not built yet.
- Chart creation depends on what the installed `mb` CLI version actually
  supports; if a capability isn't available, Claude will say so rather than
  working around it with a different interface.
