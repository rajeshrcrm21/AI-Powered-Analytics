# AI-Powered Advanced Analytics Recommendation Engine

A workflow driven entirely by talking to Claude directly in VS Code — no web
UI, no backend, no database of its own — that uses Claude + the Metabase CLI
(`mb`) to build professional, well-optimized charts and dashboards (with
custom drill-downs and other Metabase-native features) against a Recruit CRM
customer's actual analytics data, plus a dedicated documentation tab (built
from Metabase's own text cards, not a separate document) on each dashboard
explaining it for the people who'll actually use it.

Everything happens by talking to Claude in VS Code — describe what you need
(a stated requirement, a pasted transcript, an attached PDF/image, or several
combined) and Claude builds it. There is nothing to `npm install` or `run`.

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
2. Ask which kind of work you want: **Requirements Intake** (you share chart
   requirements directly, in whatever form you have them — a written ask, a
   numbered list, a pasted client transcript, an attached document (PDF,
   image, etc.), or several combined — and Claude grounds each in that
   account's real data and assembles a dashboard, new or existing, with a
   documentation tab explaining it; this project's primary flow),
   **Default Dashboard** (the standardized onboarding dashboard every
   account gets, built automatically), or **Important Metrics Dashboard**
   (the standardized hiring-efficiency dashboard every account gets, also
   built automatically).

The **Requirements Intake** flow asks for the account number and your
requirements (any combination of a stated ask, a transcript, or an attached
document), checks known patterns/reference material first and falls back to
live discovery, asks a clarifying question only when a requirement is
genuinely ambiguous, and presents a numbered list of buildable charts before
asking which to create. Once confirmed, it decides where they land — a
dashboard you named, an existing dashboard it asks you about if one plausibly
already covers the same ground, or one or more new dashboards otherwise —
assembles the charts there with drill-downs, and adds a documentation tab
(built from Metabase's own text cards) explaining the dashboard for its end
users. Audio/video sources aren't processed directly — Claude will ask for a
text transcript instead, since this project has no transcription capability.

The **Default Dashboard** flow instead just asks for the account number and
runs `scripts/create_default_dashboard.py`, which discovers the account's
data and builds the standard chart set end-to-end.

The **Important Metrics Dashboard** flow works the same way: asks for the
account number and runs `scripts/create_important_metrics_dashboard.py`,
which discovers the account's data and builds its own standard chart set
(jobs & hiring efficiency, ratios, trends, candidate diversity) end-to-end.

Every discovery/resolution step in the Requirements Intake flow works from
schema metadata (table/column names, types) only — it never samples,
queries, or displays the account's actual row data. The one narrow,
documented exception is described in "Where charts touch real data" below.
The two dashboard scripts follow the same metadata-only discovery
internally.

See `docs/workflow.md` for all three flows written out in more detail, and
`CLAUDE.md` for the operating instructions Claude itself follows.

## Project structure

```
CLAUDE.md                  Persistent operating instructions for Claude
README.md                  This file
.env.example                Credential placeholders (copy to .env)
.gitignore
config/analysis-config.md  Tunable defaults (data-quality thresholds, chart-type defaults)
prompts/
  discovery.md              Map the account's actual data (metadata only)
  chart-generation.md        Create + verify one card in Metabase
  requirements-intake.md     Requirements Intake: stated ask / transcript / document (any
                              combination) -> grounded chart candidates -> dashboard
                              (new or existing) with a text-card documentation tab
  infeasible-requirement.md  How to handle a requirement the account's real data can't support
  metabase_skill_improvement.md  Prompt for building references/ (schema map, metric glossary,
                              canonical patterns) that Requirements Intake checks first once built
docs/
  architecture.md            System shape and rationale
  workflow.md                Human-readable walkthrough of all three flows
references/
  schema-map.md              Structural (metadata-only) map of the 12 core Recruit CRM tables
  metric-glossary.md         Business-term definitions confirmed by the user, per account
scripts/
  mb-login.sh                                    One-time helper: .env -> mb auth login
  create_default_dashboard.py                    Automates the Default Dashboard flow end-to-end
  default_dashboard_template.json                Fixed chart set the Default Dashboard flow replicates
  create_important_metrics_dashboard.py          Automates the Important Metrics Dashboard flow end-to-end
  important_metrics_dashboard_template.json      Fixed chart set the Important Metrics Dashboard flow replicates
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
  delivered as terminal/chat output; the only dashboard/card/document
  content that exists is what gets created in Metabase itself (Default
  Dashboard flow, Important Metrics Dashboard flow, or confirmed
  Requirements Intake charts/dashboards/documents).
- No audio/video transcription — Requirements Intake accepts a stated ask, a
  pasted transcript, and attached documents (PDF, image, etc.), but can't
  process a raw audio/video file directly. Claude will ask for a text
  transcript of it instead.
- Chart creation depends on what the installed `mb` CLI version actually
  supports; if a capability isn't available, Claude will say so rather than
  working around it with a different interface.
