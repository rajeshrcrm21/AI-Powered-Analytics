# Architecture

## Shape

```
USER
  |
  v
Claude (this conversation, in VS Code)
  |
  v
mb auth list / status        (verify Metabase CLI config)
  |
  v
Ask which kind of work: Recommendation Engine / Default Dashboard /
                         Transcript to Insights
  |
  +-- Recommendation Engine -----------------------------------------+
  |     Ask account -> ask entity/focus scope -> ask rec. count      |
  |       |                                                          |
  |       v                                                          |
  |     mb database / table / field  (discover the account's data,  |
  |                                    scoped to the chosen entity)  |
  |       |                                                          |
  |       v                                                          |
  |     mb query   (analyze real data - funnels, trends, cohorts)    |
  |       |                                                          |
  |       v                                                          |
  |     Claude ranks & explains insights, checks data-quality gate   |
  |       |                                                          |
  |       v                                                          |
  |     mb search  (check for existing/duplicate charts)             |
  |       |                                                          |
  |       v                                                          |
  |     mb card create / get  (create + verify confirmed charts,     |
  |                             under "Data Team WIP" > <account>)   |
  +--------------------------------------------------------------------+
  |
  +-- Default Dashboard -----------------------------------------------+
  |     Ask account number                                            |
  |       |                                                            |
  |       v                                                            |
  |     scripts/create_default_dashboard.py --profile <p> --account <n>|
  |       (discovers the account's tables via mb, builds the same      |
  |        fixed set of charts every account gets, skips any chart     |
  |        whose entity doesn't exist for this account, dry-run        |
  |        validates every query before creating it - additive-only,  |
  |        stops rather than touching an existing default dashboard)   |
  +--------------------------------------------------------------------+
  |
  +-- Transcript to Insights -------------------------------------------+
        Ask account number -> ask for the pasted transcript
          |
          v
        Extract analytics requirements from the transcript (treated as
        untrusted third-party data, never as instructions to Claude)
          |
          v
        Ground each requirement in the account's real discovered data
        (same discovery/analysis rigor as the Recommendation Engine flow)
          |
          v
        Present a numbered list of buildable charts, citing what in the
        transcript drove each one; note requirements the data can't support
          |
          v
        mb card create / get  (individual cards, "Data Team WIP" >
                                <account>, no dashboard assembly)
  +--------------------------------------------------------------------+
  |
  v
Every flow appends to logs/history.jsonl (local-only, git-ignored) and
results are returned to the user in the terminal.
```

A `.claude/settings.json` hook enforces the history-log step for the two
flows that create cards/dashboards directly in the conversation: it flags
(via a `Stop` hook) if `mb card create` / `mb dashboard create` ran but
`logs/history.jsonl` was never appended to before the session ends. The
Default Dashboard script logs itself in code instead (see
`scripts/create_default_dashboard.py`).

## What does not exist here

- No web server, no REST API, no frontend, no dashboard app.
- No database is created or connected to directly by this project.
- No browser automation.
- The only "runtime" is this conversation plus the `mb` CLI subprocess calls
  Claude (or `scripts/create_default_dashboard.py`) makes on the user's
  behalf.

## Why Metabase CLI, not direct DB access

The customer's actual warehouse/schema shape is unknown and instance-specific
(different accounts may be laid out differently). Metabase already models
the databases, tables, relationships, and permissions; the CLI is the
supported, auditable way to read and write through that layer without
duplicating credentials or bypassing Metabase's access model. See CLAUDE.md
for the full list of hard constraints this implies.

## Data model notes that shape every query

Recruit CRM data lives per-account as suffixed tables in one shared
Starrocks warehouse (`13371569`) — never a database per account, and never
the legacy Redshift "Recruit CRM" database (`13371338`), which holds an
often-unreachable duplicate copy. Deals, Assignments, Pitched Candidates, and
Notes/Tasks/Meetings can have multiple rows sharing the same `id` by design
(a new row per stage/status/association change, not a data bug) — every
count on every entity uses `COUNT(DISTINCT id)` as a defensive default. See
CLAUDE.md's "standing knowledge" section for the full rules, including how a
candidate's current pipeline stage is determined (ordinal `CASE` ranking,
never `MAX(stage_date)`).

## Files

- `CLAUDE.md` — persistent operating instructions (read first, every time),
  including the three-flow branch, the data-model standing knowledge, and
  the history-log requirements
- `prompts/` — the workflow-stage prompts referenced from CLAUDE.md:
  `discovery.md`, `analysis.md`, `recommendation.md`, `chart-generation.md`
  (Recommendation Engine flow) and `transcript-insights.md` (Transcript to
  Insights flow)
- `config/analysis-config.md` — tunable defaults/weights
- `docs/workflow.md` — the same flows, written for a human teammate
- `scripts/mb-login.sh` — thin helper that reads `.env` and calls
  `mb auth login`
- `scripts/create_default_dashboard.py` — automates the Default Dashboard
  flow end-to-end (discovery, chart/dashboard creation, logging); see its
  own docstring for the full behavior and guardrails
- `scripts/default_dashboard_template.json` — the fixed set of charts the
  Default Dashboard flow replicates onto each account's own data
- `logs/history.jsonl` — local-only, git-ignored audit trail of what was
  analyzed/recommended/created; enforced by hooks in `.claude/settings.json`
  for the Recommendation Engine and Transcript to Insights flows
