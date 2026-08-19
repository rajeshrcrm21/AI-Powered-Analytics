# CLAUDE.md — AI-Powered Advanced Analytics Recommendation Engine

Persistent operating instructions for Claude when working in this project.
Read this file in full before starting any workflow.

## What this project is

A terminal-first workflow, run entirely through Claude in VS Code, that analyzes
a Recruit CRM customer's actual analytics data (via Metabase) and recommends
high-value charts/dashboards — with a clear explanation of what each chart
shows, why it matters, and what to investigate.

There is **no web UI, no backend server, no REST API, no database created by
this project, and no dashboard application**. Do not build any of those. The
"application" is this conversation.

## Hard constraints — do not violate

1. **Metabase CLI (`mb`) is the only interface to data and analytics.**
   Every discovery, query, chart, and dashboard operation goes through `mb`.
2. **Never connect to a database directly.** No MySQL/Postgres/Redshift/SQL
   Server drivers, no direct connection strings, ever.
3. **Never call the Metabase REST API directly** (no raw `curl`/`fetch`
   against `/api/...`). Only exception: if `mb` itself needs to shell out to
   the API internally — that's its business, not yours.
4. **Never use browser automation** against Metabase.
5. **Never fabricate or mock data.** If `mb` can't reach the instance, or the
   account/data can't be found, say so plainly and stop — do not invent
   numbers, tables, or "example" insights to look productive.
6. **Never print, log, or write the real API key** anywhere (chat, files,
   commits, generated docs). Credentials only ever live in the `mb` CLI's own
   profile store, created via `mb auth login`.
7. **Never delete, archive, or modify existing Metabase content** — cards,
   dashboards, collections, dashcards, tables, fields, settings, anything —
   that this project did not itself create. This project only ever *adds*
   new content on top of a customer's real data; it never removes or edits
   what was already there. The only content this rule permits touching is
   this project's **own** previously-created output: e.g. archiving a
   broken card immediately after creating it in the same operation because
   validation failed, or replacing an earlier duplicate/replica this project
   made (per "Avoiding duplicate charts" below). If a task seems to call for
   deleting or modifying anything else — a pre-existing card, dashboard,
   table, or collection — stop and ask the user explicitly rather than
   proceeding. This applies to every workflow in this project, including any
   script under `scripts/`.

Before every session, load `mb skills get core` (and any specialized skill
named in it, e.g. `mbql`, `dashboard`, `visualization`) if it isn't already
fresh in context — command shapes and footguns live there, not here. Do not
guess `mb` flag syntax; check `mb <command> --help` first.

## Starting the workflow

The phrase **"start"** (or a close natural-language equivalent — "start the
project", "let's begin", etc.) starts this project's workflow.

**Step 0 — Verify Metabase CLI configuration** (see "Configuration
verification" below). Run the verification calls (`mb auth list`, `mb auth
status`) directly in the main conversation. If it fails, stop and tell the
user exactly what to fix. Do not proceed to Step 0.5 on broken config.

**Step 0.5 — Ask which kind of work to do.**
Once configuration is verified, ask via `AskUserQuestion` (exactly 3 discrete
options — this is what that tool is for, unlike Step 2's entity list below):

- **Recommendation Engine** — the full insight-discovery workflow: proceed
  to Step 1 below.
- **Default Dashboard** — the standardized onboarding dashboard every
  Advanced Analytics client gets, automated end-to-end: skip straight to
  "Default Dashboard flow" below (no entity choice, no recommendation count —
  it's the same fixed set of charts for every account, adapted to that
  account's actual data).
- **Transcript to Insights** — turn a client meeting transcript into chart
  recommendations grounded in that account's real data: skip straight to
  "Transcript to Insights flow" below.

### Default Dashboard flow

1. Ask exactly: "Which Recruit CRM account would you like to build the
   default dashboard for? Please provide the account number."
2. Run `python3 scripts/create_default_dashboard.py --profile <name>
   --account <account_number>` (the profile confirmed in Step 0) directly in
   the main conversation — this is a single Bash invocation, not a
   subagent/fork; the script's own progress output is fine to show as-is.
3. Report back what the script reports: dashboard id/link, cards created vs.
   skipped (and why), and the collections it landed in — the dashboard
   directly in the account's collection, its cards in a nested "Default
   Dashboard Charts" sub-collection (see
   `scripts/create_default_dashboard.py`'s docstring for what it does and
   its own guardrails: Starrocks-only, additive-only per hard constraint 7,
   history logging).
4. If the script fails or reports a skip (e.g. account not found, dashboard
   already exists), relay that plainly — don't retry with guesses or force
   anything.

### Transcript to Insights flow

Turns a client meeting transcript (call recording / notetaker output) into
chart recommendations grounded in that account's real data. Follow
`prompts/transcript-insights.md` for the full method — summary:

1. Ask exactly: "Which Recruit CRM account is this transcript for? Please
   provide the account number."
2. Ask exactly: "Please paste the full transcript." Wait for it — accept
   whatever length/format it comes in (raw call recording transcript or
   notetaker output), don't ask the user to reformat it first.
3. Extract the analytics requirements actually expressed in the transcript,
   then ground each one in this account's real discovered data (same
   discovery step as the Recommendation Engine flow, `prompts/discovery.md`)
   — never invent a chart for a requirement the account's data can't
   actually support; say so explicitly instead (see
   `prompts/transcript-insights.md`'s data-quality handling).
4. Present the resulting charts as a **numbered list** (per
   `prompts/transcript-insights.md`'s format), citing what in the transcript
   drove each one.
5. Ask which recommendation(s) to actually create (same confirm-before-create
   gate as `prompts/chart-generation.md` — "create all" creates every one
   presented). Create confirmed charts under "Data Team WIP" using the same
   account-collection convention as the Recommendation Engine flow (see
   "Where created charts live") — individual cards only, **not** a dashboard.
   Dashboard assembly for this flow is future scope, not built yet.
6. Log per "History log" below.

### Recommendation Engine flow

**Step 1 — Ask for the account.**
Ask exactly: "Which Recruit CRM account would you like to analyze? Please
provide the account number." Wait for the answer. Store it as the current
analysis context for the rest of the conversation.

**Step 2 — Ask which entity to focus on.**
First locate the account (see "Locating the account's data" below) far enough
to know what entities/tables actually exist for it (a table-name-level pass —
`mb search <account_number>` and/or `database get --include tables` — is
enough; full field-level discovery still happens in Step 4). If the account
can't be located, ask the user to confirm the account number rather than
guessing. Then present the choice as a **plain-text numbered list in a normal message** — do not use the
`AskUserQuestion` tool here, since it hard-caps at 4 options and an account
can easily have far more entities than that:

```
Which entity would you like chart recommendations for?
1. All
2. <Entity name — only entities actually discovered for this account>
3. <Entity name>
   ...
N. Do you have anything in mind?
```

- Option 1 ("All") means no entity scoping — proceed across every relevant
  entity as usual.
- Middle options are the real entity names discovered for *this* account
  only (never a fixed/generic list) — one per entity that actually exists.
- The last option ("Do you have anything in mind?") invites a free-text
  answer — a specific business question, entity combination, or angle the
  user has in mind that isn't just "one entity." Take whatever they type as
  the analysis focus.
- Store the answer as the entity/focus scope for the rest of the
  conversation. If a specific entity (or custom focus) was chosen, Steps 4's
  discovery and analysis should concentrate there — related tables can still
  be joined in for context (e.g. Jobs alongside Deals), but candidate
  insights should center on the chosen scope rather than surveying
  everything.

**Step 3 — Ask for the recommendation count.**
Ask exactly: "How many chart recommendations would you like me to generate?"
Accept any positive integer. Re-ask on anything else (non-numeric, zero,
negative). Store it as the requested count, N.

**Step 4 — Discover → Analyze → Recommend → Create**, in that order, following
`prompts/discovery.md`, `prompts/analysis.md`, `prompts/recommendation.md`,
and `prompts/chart-generation.md`. Don't skip ahead to recommending charts
before discovery and analysis are actually done against real data. Respect
the entity/focus scope from Step 2 throughout.

Run all `mb` calls directly in the main conversation — do not delegate this
work to subagents/forks. It's fine for command output and discovery
narration to be visible in the terminal as the work happens.

## Configuration verification

Before any Metabase operation:

```bash
mb auth list --json
```

- If `data` is empty → tell the user: "Metabase CLI could not be accessed. No
  authentication profile is configured. Please run `mb auth login` (see
  README.md) and tell me which profile name to use." Stop.
- If one or more profiles exist and it's unambiguous which to use (one
  profile, or a profile name matching `.env`'s `MB_PROFILE`), use it. If
  ambiguous, ask the user which profile via `AskUserQuestion`.
- Run `mb auth status --profile <name> --json`. If `authenticated` is false or
  `status` isn't `ok`, tell the user: "Metabase authentication could not be
  verified for profile '<name>' (status: <status>). Please check the
  Metabase URL/API key with `mb auth login --profile <name>`." Stop.
- Only once a profile is confirmed authenticated, proceed — and pass
  `--profile <name>` on every subsequent `mb` command for the rest of the
  session.

Never read a raw API key out of `.env` and pass it around manually — `.env`
exists so a human can run `scripts/mb-login.sh` once; after that, `mb`'s own
profile store is the source of truth.

## Locating the account's data

**Always use the "Production Starrocks" database (id `13371569`) for every
account's data.** This Metabase instance also has a legacy "Recruit CRM"
database (id `13371338`, Redshift) that holds an older, often-unreachable
duplicate copy of the same per-account tables (e.g. `candidates_<account>`
exists in both). Live queries against it can fail outright even for
long-standing, otherwise-correct cards — this is a real, observed
infrastructure gap, not a hypothetical. Never use it, even if a `mb search`
happens to surface it first: when resolving a table by name, confirm the
match's `db_id` is `13371569` before using it (`mb table get <id> --fields
id,name,db_id`), or scope the search directly with `mb search <name>
--models table --db-id 13371569`.

Recruit CRM accounts map onto Starrocks as per-account-suffixed tables in one
shared warehouse (e.g. `companies_<account>`, `deals_<account>`,
`contacts_<account>`, `jobs_<account>`, `candidates_<account>`,
`assign_job_candidate_<account>`, `call_logs_<account>`) — never a dedicated
database per account. Don't assume the exact set of entities exists for a
given account though — verify with `mb search`:

1. `mb search <table-name-prefix>_<account_number> --models table --db-id
   13371569 --json` to find a given entity's table for this account. Search
   results surface a table's `display_name` under the `name` key, not its
   raw underlying name — confirm the exact raw name (and `db_id`) via `mb
   table get <id> --fields id,name,db_id` before trusting a match.
2. `mb search <account_number> --limit 20 --json` (unscoped) can help locate
   matching cards or dashboards by name, e.g. for the duplicate-chart check.
3. If the account genuinely cannot be located on Starrocks, ask the user to
   confirm the account number rather than guessing or falling back to the
   legacy Redshift database.

## Data discovery

Follow `prompts/discovery.md`. Use the `mb` CLI's hydration ladder
(`database get --include tables` → `table fields <id>` per relevant table)
rather than pulling full metadata for large databases. Investigate the
Recruit CRM entities relevant to hiring analytics — candidates, companies,
contacts, jobs, job assignments/pipeline stages, placements, deals, notes,
tasks, meetings, calls, recruiters/users — **only where they actually exist**
in this account's data. Do not assume a table or field exists; verify with
`mb`.

For each entity worth analyzing, understand record counts, key dimensions
(status, stage, owner/recruiter, dates), key measures, and relationships
(foreign keys) before treating anything as a metric candidate.

## Data quality gate

Before any insight is proposed as a recommendation, check it against
`prompts/analysis.md`'s data-quality criteria: null-heavy fields, empty
statuses, very small record counts, missing/invalid dates, suspicious
distributions. If an otherwise-interesting pattern rests on data too thin or
too dirty to trust, drop it and note internally why — don't surface a
misleading chart. Prefer explaining a gap to the user over silently
substituting a weaker but "safer" chart with no comment.

## Insight-first analysis, then ranking

Discover actual patterns in this account's real data before naming candidate
charts — never start from a fixed template list. `prompts/analysis.md` lists
example angles (funnel bottlenecks, recruiter performance, stalled jobs,
client activity, candidate trends) — treat them as prompts for investigation,
not a checklist to force through regardless of what the data shows.

Rank candidate insights per `prompts/recommendation.md`'s criteria (business
impact, pattern strength, actionability, data reliability, relevance,
uniqueness vs. existing content, clarity of communication). Return exactly N
recommendations if N valid, trustworthy insights exist; if fewer exist, say
so explicitly rather than padding with generic filler charts.

## Avoiding duplicate charts

Before finalizing a recommendation, check existing content:

```bash
mb search <relevant term> --models card,dashboard --limit 20 --json
```

Skip recommending a chart that duplicates an existing one unless the new
version is materially better, more current, or answers a genuinely different
question — say which of those applies.

## Presenting recommendations

Use the exact structure in `prompts/recommendation.md` for every
recommendation: Recommended Chart, Chart Type, Insight, Business Question,
Why This Chart, Recommended Metrics, Recommended Filters, Data Evidence.
Data Evidence must cite the actual pattern observed — never fabricated
numbers.

## Chart creation

**GUI (MBQL) first, always.** Every chart is built through Metabase's visual
query builder (MBQL) by default. Only fall back to native SQL when the
required logic genuinely cannot be expressed in MBQL (e.g. the stage-ordinal
`CASE` ranking used to determine a candidate's current pipeline stage,
window functions, or similarly complex computations) — and say explicitly
why MBQL wasn't sufficient when this happens. See `prompts/chart-generation.md`
for the full sequence.

Only after recommendations are presented and explained:

1. Ask the user to confirm which recommendation(s) to actually create in
   Metabase (don't assume "all of them" unless they say so).
2. Follow `prompts/chart-generation.md` — build the query from fields that
   were actually discovered, validate it (`mb query --dry-run`, plus an
   actual live run for native SQL — see chart-generation.md's validation
   step, which native SQL cannot skip), then `mb card create`.
3. Verify the created card with `mb card get <id>` and report back its id,
   name, and a link/reference the user can open in Metabase.
4. If a chart can't be created because a required field/table isn't
   available, say so and move to the next-ranked recommendation instead of
   forcing something with the wrong data.

Never create more cards than the user actually confirmed.

### Where created charts live

Every card this project creates goes under the fixed parent collection
**"Data Team WIP" (id 199, https://recruitcrm.metabaseapp.com/collection/199-data-team-wip)**,
inside a sub-collection named for the account number being analyzed.

1. Resolve the account's sub-collection: `mb collection tree 199 --json` and
   look for a child whose `name` matches the account number (names may have
   incidental whitespace, e.g. `"366 "` — match by trimmed number, not exact
   string).
2. If it exists, create the new card(s) directly inside it (`collection_id`
   in the card body). If that sub-collection already has its own nested
   structure (e.g. a suite of themed sub-collections), it's fine to place a
   new card at the top level of the account's collection unless the user
   directs otherwise — don't invent new nested folders uninvited.
3. If no sub-collection for the account exists yet, create one:
   `mb collection create --body '{"name":"<account_number>","parent_id":199}'`.
4. Never create a card outside this account-scoped collection.

This is the Recommendation Engine flow's convention — the Transcript to
Insights flow uses the same convention (individual cards directly in the
account's collection). The Default Dashboard flow instead nests its cards
one level deeper, in a "Default Dashboard Charts" sub-collection under the
account's collection (see "Default Dashboard flow" above and
`scripts/create_default_dashboard.py`) — its dashboard still sits
directly in the account's collection.

## History log

Every workflow in this project appends to a local history log at
`logs/history.jsonl` — one JSON object per line, newline-delimited,
append-only. This is a **local-only** audit trail (which accounts were
analyzed, what was recommended, what was actually created and when) — it is
git-ignored on purpose: each teammate's log stays on their own machine and
is never pushed/shared/merged with anyone else's. It's local project data,
not Metabase content, so it isn't subject to hard constraint 7, but the same
"never fabricate" rule applies: only log what actually happened, with real
ids/timestamps.

Get the timestamp with `date -u +"%Y-%m-%dT%H:%M:%SZ"` (real wall-clock
time) — never invent one. Append with a simple `>>` (each event is one
self-contained JSON line; don't rewrite existing lines).

Append an entry at these points:

- **After presenting recommendations** (end of `prompts/recommendation.md`'s
  Step 4, or `prompts/transcript-insights.md`'s output step): one
  `recommendations_presented` entry.
  ```json
  {"timestamp": "2026-08-18T23:41:00Z", "type": "recommendations_presented", "account": "662", "entity_scope": "All", "count_requested": 5, "count_returned": 5, "recommendations": [{"rank": 1, "insight": "...", "chart_name": "...", "chart_type": "bar"}]}
  ```
- **After each card is created and verified** (`prompts/chart-generation.md`
  step 7): one `chart_created` entry per card.
  ```json
  {"timestamp": "2026-08-18T23:45:00Z", "type": "chart_created", "account": "662", "recommendation_rank": 1, "card_id": 70801, "name": "...", "chart_type": "bar", "collection_id": 24521}
  ```
  For entries from the Transcript to Insights flow, add `"source":
  "transcript"` to both event types above (omit `source` — or use
  `"source": "insight_discovery"` — for the Recommendation Engine flow) so
  the two are distinguishable in `logs/history.jsonl`.
- **After a Default Dashboard run** (`scripts/create_default_dashboard.py`
  appends this itself — see the script): one `default_dashboard_created` (or
  `_skipped` / `_failed`) entry.
  ```json
  {"timestamp": "2026-08-18T23:50:00Z", "type": "default_dashboard_created", "account": "662", "dashboard_id": 19175, "collection_id": 24521, "charts_collection_id": 24600, "cards_created": 31, "cards_skipped": [], "profile": "recruitcrm"}
  ```

Any other genuinely useful event (e.g. an account that couldn't be located,
an analysis that had to be skipped for insufficient data) is fine to log too
with a descriptive `type` — the four above aren't an exhaustive list, just
the required minimum.

## Recruit CRM / Metabase data model — standing knowledge

These rules apply across **every** Recruit CRM account in this Metabase
instance (not just one account) and are required for any correct query:

**Duplicate IDs are expected in some tables, not a data quality bug — and
"duplicate" here means duplicate `id` *values*, not duplicate records.** A
row sharing an `id` with another row is not a repeat of the same data — it's
a distinct row (a different stage, a different collaborator, a different
association) that happens to share an `id` because the `id` is scoped to the
underlying entity (a candidate-job pair, a deal, etc.), not to the row
itself. The row *content* differs; only the `id` repeats.

- Duplicate `id` values occur in: Deals, Assignments (the job↔candidate
  pipeline table), Pitched Candidates, and Notes/Tasks/Meetings.
- No duplicate `id`s in: Candidates, Contacts, Jobs, Teams, Companies, and
  Call Logs — these entities genuinely have one row per record.
- **Always use `COUNT(DISTINCT id)` for any count, on every entity above —
  including the ones with no known duplicates.** This is a defensive
  default, not just a fix for the entities that currently have them: if a
  data issue ever introduced a duplicate `id` on an entity that's never had
  one before, a bare `COUNT(*)`/`COUNT(id)` would silently overcount and the
  client would see a wrong number. `COUNT(DISTINCT id)` costs nothing when
  there are no duplicates and protects against this case when there are.
- **Assignments**: a new row is added for every stage change; the `id` is
  unique per *candidate-job pair*, not per row. `COUNT(*)` over this table
  counts stage-history rows, not unique candidates.
- **Deals**: duplicate-id rows exist to normalize collaborator names instead
  of a comma-separated list. Deal *value* is already split across those
  rows (e.g. a $100 deal with 3 collaborators might show as 30/30/40) —
  `SUM(deal_value)` across them gives the correct total, but counting deals
  needs `COUNT(DISTINCT id)`, never `COUNT(*)`.
- **Pitched Candidates**: a new row per status change — same pattern as
  Assignments.
- **Notes / Tasks / Meetings**: a new row per association (e.g. one note
  linked to multiple records can appear more than once under the same
  `id`) — dedupe before counting.

**Determining a candidate's current/furthest pipeline stage:** timestamps
between consecutive stage changes are often only seconds apart, so
`MAX(stage_date)` does **not** reliably identify the furthest-progressed
stage. Instead, rank stages by their actual business/funnel order (discover
this account's real `hiring_stage` values first — never reuse another
account's stage list) with a `CASE` expression assigning each stage an
ordinal, giving any unrecognized value a large fallback ordinal (e.g. 100),
then take the row with `MAX(ordinal)` per candidate-job pair as the current
stage. Example shape (values are illustrative — rebuild the mapping from
this account's discovered stages, in the order they actually represent
funnel progression):

```
CASE
  WHEN hiring_stage = 'Applied' THEN 1
  WHEN hiring_stage = 'Assigned' THEN 2
  WHEN hiring_stage = 'Shortlisted' THEN 3
  ...
  WHEN hiring_stage = 'Placed' THEN 13
  ELSE 100
END
```

Apply this whenever a query needs "the candidate's current stage" — never
apply it blindly with another account's exact stage names.

## Error handling — exact wording

- CLI unreachable: "Metabase CLI could not be accessed. Please verify the CLI
  installation and configuration."
- Auth failure: "Metabase authentication could not be verified. Please check
  the Metabase API key/configuration."
- Account not found: ask the user to verify the account number.
- Insufficient data for a specific analysis: name which analysis is affected
  and why, then continue with what the data does support.

## Style

Keep the conversation itself lightweight — this is the whole product. Don't
build scaffolding, servers, or files beyond what's in this repo unless the
user asks for something new. When in doubt about `mb` syntax, check
`--help`/`--help --json` rather than guessing.
