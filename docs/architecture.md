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
Ask which kind of work: Requirements Intake /
                         Default Dashboard / Important Metrics Dashboard
  |
  +-- Requirements Intake (primary flow) --------------------------------+
  |     Ask account -> ask "Data Team WIP" or the account's own          |
  |     collection (every time) -> ask for requirements: a stated ask, a |
  |     pasted transcript, an attached document (PDF/image), or several  |
  |     combined                                                         |
  |     (all treated as untrusted third-party data to mine for           |
  |     requirements, never as instructions to Claude; audio/video isn't |
  |     processed directly - Claude asks for a text transcript instead)  |
  |       |                                                              |
  |       v                                                              |
  |     Resolve each requirement: references/canonical-patterns.md ->    |
  |     references/schema-map.md / metric-glossary.md -> live discovery  |
  |     (mb database / table / field - metadata only, never row values)  |
  |       |                                                              |
  |       v                                                              |
  |     Ask a clarifying question only when genuinely ambiguous          |
  |     (never by querying live data to check)                           |
  |       |                                                              |
  |       v                                                              |
  |     mb search  (check for existing/duplicate charts, name-level only)|
  |       |                                                              |
  |       v                                                              |
  |     Present numbered list -> confirm -> mb card create / get         |
  |     (individual cards, in whichever collection was chosen: "Data     |
  |     Team WIP" > <account>, or the account's own collection)          |
  |       |                                                              |
  |       v                                                              |
  |     Choose dashboard destination: a named existing dashboard, an     |
  |     existing dashboard confirmed by asking (mb search surfaced one), |
  |     or one/more new dashboards (best grouping, unless user says      |
  |     otherwise) - updating an existing one is additive-only, never    |
  |     touching what's already on it (hard constraint 7's exception)    |
  |       |                                                              |
  |       v                                                              |
  |     Assemble confirmed cards onto the chosen dashboard(s) - layout,  |
  |     shared filters, drill-downs (click_behavior)                     |
  |     (mb dashboard create / update, verified with mb dashboard get)   |
  |       |                                                              |
  |       v                                                              |
  |     Add a documentation tab (new dashboard tab, text-card dashcards  |
  |     only - card_id: null, virtual_card.display: "text") explaining   |
  |     the dashboard's purpose, metrics, and how to use it, for its     |
  |     end users - verified with mb dashboard get                       |
  +------------------------------------------------------------------------+
  |
  +-- Default Dashboard -----------------------------------------------+
  |     Ask account number                                            |
  |       |                                                            |
  |       v                                                            |
  |     scripts/create_default_dashboard.py --profile <p> --account <n>|
  |       (discovers the account's tables via mb, builds the same      |
  |        fixed set of charts every account gets, skips any chart     |
  |        whose entity doesn't exist for this account, dry-run        |
  |        validates every query before creating it - always in the    |
  |        account's own collection, pinned there, never "Data Team    |
  |        WIP" - additive-only, stops rather than touching an         |
  |        existing default dashboard, in either collection)           |
  +--------------------------------------------------------------------+
  |
  +-- Important Metrics Dashboard ---------------------------------------+
  |     Ask account number                                               |
  |       |                                                               |
  |       v                                                               |
  |     scripts/create_important_metrics_dashboard.py                    |
  |       --profile <p> --account <n>                                    |
  |       (discovers the account's tables via mb, builds the same        |
  |        fixed set of hiring-efficiency/ratio/trend/diversity charts   |
  |        every account gets, remapping fields/tables per entity for    |
  |        cards that span more than one - e.g. jobs<->assignments       |
  |        joins - skips any chart whose entity doesn't exist for this   |
  |        account, dry-run validates every query before creating it -   |
  |        always in the account's own collection, pinned there, never   |
  |        "Data Team WIP" - additive-only, stops rather than touching an |
  |        existing important metrics dashboard, in either collection)   |
  +--------------------------------------------------------------------+
  |
  v
Every flow appends to logs/history.jsonl (local-only, git-ignored) and
results are returned to the user in the terminal.
```

A `.claude/settings.json` hook enforces the history-log step for the
conversational flow (Requirements Intake) that creates/updates
cards/dashboards directly in the conversation: it flags (via a `Stop` hook)
if `mb card create` / `mb dashboard create` / `mb dashboard update` ran but
`logs/history.jsonl` was never appended to before the session ends. The
Default Dashboard and Important Metrics Dashboard scripts log themselves in
code instead (see `scripts/create_default_dashboard.py` and
`scripts/create_important_metrics_dashboard.py`).

## What does not exist here

- No web server, no REST API, no frontend, no dashboard app.
- No database is created or connected to directly by this project.
- No browser automation.
- The only "runtime" is this conversation plus the `mb` CLI subprocess calls
  Claude (or `scripts/create_default_dashboard.py` /
  `scripts/create_important_metrics_dashboard.py`) makes on the user's
  behalf.

## Additive-only, with one narrow exception

This project never deletes, archives, or modifies existing Metabase content
it didn't create (hard constraint 7). The one exception: Requirements Intake
may add new cards and a new documentation tab to an **existing** dashboard —
including one this project didn't create — when the user names that
dashboard or confirms doing so after being asked (see CLAUDE.md "Dashboard
destination"). Even there it stays additive: only ever add alongside what's
already on the dashboard, never rearrange, resize, remove, or edit an
existing tab, dashcard, or filter.

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
  `discovery.md` and `chart-generation.md` (shared by every flow),
  `requirements-intake.md` (Requirements Intake flow: stated ask / transcript
  / document, in any combination, through dashboard destination, assembly,
  and its text-card documentation tab), and `infeasible-requirement.md`
  (shared handling for a requirement the data can't support)
- `references/` — `schema-map.md` (structural, metadata-only map of the core
  tables) and `metric-glossary.md` (business-term definitions confirmed by
  the user, per account) — checked before falling back to live discovery
- `config/analysis-config.md` — tunable defaults (data-quality thresholds,
  chart-type defaults)
- `docs/workflow.md` — the same flows, written for a human teammate
- `scripts/mb-login.sh` — thin helper that reads `.env` and calls
  `mb auth login`
- `scripts/create_default_dashboard.py` — automates the Default Dashboard
  flow end-to-end (discovery, chart/dashboard creation, logging); see its
  own docstring for the full behavior and guardrails
- `scripts/default_dashboard_template.json` — the fixed set of charts the
  Default Dashboard flow replicates onto each account's own data
- `scripts/create_important_metrics_dashboard.py` — automates the Important
  Metrics Dashboard flow end-to-end (discovery, chart/dashboard creation,
  logging); see its own docstring for the full behavior and guardrails,
  including how it remaps fields/tables per entity for cards spanning more
  than one, and its one native-SQL card (a window-function time-in-stage
  calculation that MBQL can't express)
- `scripts/important_metrics_dashboard_template.json` — the fixed set of
  charts the Important Metrics Dashboard flow replicates onto each
  account's own data
- `logs/history.jsonl` — local-only, git-ignored audit trail of what was
  analyzed/recommended/created; enforced by hooks in `.claude/settings.json`
  for the Requirements Intake flow
