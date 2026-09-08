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
Once configuration is verified, ask via `AskUserQuestion` (2 discrete
options — this is what that tool is for, unlike Step 2's entity list below):

- **Requirements Intake** — the user states chart requirements directly
  (a single ask, a numbered list, a pasted client doc) rather than a
  transcript: skip straight to "Requirements Intake flow" below. This is
  this project's primary flow.
- **Transcript to Insights** — turn a client meeting transcript into chart
  recommendations grounded in that account's real data: skip straight to
  "Transcript to Insights flow" below.

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
   then ground each one in this account's real discovered data (the same
   discovery step described in `prompts/discovery.md`) — never invent a
   chart for a requirement the account's data can't actually support; say so
   explicitly instead (see `prompts/transcript-insights.md`'s data-quality
   handling).
4. Present the resulting charts as a **numbered list** (per
   `prompts/transcript-insights.md`'s format), citing what in the transcript
   drove each one.
5. Ask which recommendation(s) to actually create (same confirm-before-create
   gate as `prompts/chart-generation.md` — "create all" creates every one
   presented). Create confirmed charts under "Data Team WIP" using the
   account-collection convention described in "Where created charts live"
   below — individual cards only, **not** a dashboard. Dashboard assembly
   for this flow is future scope, not built yet.
6. Log per "History log" below.

### Requirements Intake flow

Turns requirements the user states directly — not a transcript, not
open-ended discovery — into chart recommendations grounded in that account's
real data. Follow `prompts/requirements-intake.md` for the full method —
summary:

1. Ask exactly: "Which Recruit CRM account are these requirements for?
   Please provide the account number."
2. Ask exactly: "Please share your chart requirements — a single ask, a
   numbered list, or a pasted client doc listing several." Accept whatever
   format it comes in.
3. Resolve each requirement in order: check `references/canonical-patterns.md`
   for a known shape first (if it exists), then `references/schema-map.md`/
   `references/metric-glossary.md`, then fall back to live discovery per
   `prompts/discovery.md` — in full, never invent a chart for a requirement
   the account's data can't actually support (say so explicitly instead).
   Group requirements that share an entity/model before building.
4. Ask a clarifying question only when a requirement is genuinely ambiguous
   in a way that changes the query (per `prompts/requirements-intake.md`'s
   "When to actually ask a question") — never as a general hedge.
5. Present the resulting charts as a **numbered list** (per
   `prompts/requirements-intake.md`'s format), citing which requirement drove
   each one.
6. Ask which recommendation(s) to actually create (same confirm-before-create
   gate as `prompts/chart-generation.md` — "create all" creates every one
   presented; resolve any open questions before creating a card that had
   one). Create confirmed charts under "Data Team WIP" using the
   account-collection convention described in "Where created charts live"
   below — individual cards only, **not** a dashboard.
7. Log per "History log" below.

## Locating the account's data

Recruit CRM data lives per-account as suffixed tables (e.g.
`candidates_662`, `jobs_662`) in one shared Starrocks warehouse (db id
`13371569`) — never a database per account, and never the legacy Redshift
"Recruit CRM" database (`13371338`), which holds an often-unreachable
duplicate copy. Given an account number, confirm it exists before doing
anything else:

```bash
mb search <account_number> --models table --db-id 13371569 --limit 20 --json
```

Confirm at least one result is a real table (e.g. `candidates_<account_number>`)
with `db_id: 13371569` — a name match on the wrong database doesn't count.
This is purely a metadata/existence check (table names, not row content). If
nothing matches, tell the user the account couldn't be found (per "Error
handling" below) rather than guessing or proceeding on an unconfirmed
account number.

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

Before any chart is presented as a recommendation, check it against these
data-quality criteria: null-heavy fields, empty statuses, very small record
counts, missing/invalid dates, suspicious distributions (thresholds in
`config/analysis-config.md`, e.g. treat under ~20 records in a slice as too
small to trust). If an otherwise-buildable chart rests on data too thin or
too dirty to trust, drop it and note internally why — don't surface a
misleading chart. Prefer explaining a gap to the user over silently
substituting a weaker but "safer" chart with no comment.

## Avoiding duplicate charts

Before finalizing a recommendation, check existing content:

```bash
mb search <relevant term> --models card,dashboard --limit 20 --json
```

Skip recommending a chart that duplicates an existing one unless the new
version is materially better, more current, or answers a genuinely different
question — say which of those applies.

**This check is name/description-level only — never open a matched card's
saved query (`mb card get <id>`, its `dataset_query`) to mine business
values out of it** (a hiring-stage order from its `CASE` expression, a
category literal from its filters, etc.). That's a side door back to
"discovering real values without asking" — the same thing forbidden
elsewhere in this file for live field queries, just via an existing card
instead of the raw table. A term's values, order, or definition come only
from the user or `references/metric-glossary.md`, never from what an old
card happens to already encode, no matter how plausible it looks.

## Chart creation

**GUI (MBQL) first, always.** Every chart is built through Metabase's visual
query builder (MBQL) by default. Only fall back to native SQL when the
required logic genuinely cannot be expressed in MBQL (e.g. the stage-ordinal
`CASE` ranking used to determine a candidate's current pipeline stage,
window functions, or similarly complex computations) — and say explicitly
why MBQL wasn't sufficient when this happens. See `prompts/chart-generation.md`
for the full sequence.

When native SQL genuinely is necessary, don't ship it as a one-off raw-SQL
question: save it as a **Model** first, then build the actual chart on top
of that Model through the GUI/MBQL editor, so the result stays drillable and
editable like any other question. Weigh this against clutter, though — don't
promote every one-off SQL question to its own Model. Only do it when the
underlying logic is genuinely reusable across more than one likely question
(e.g. the stage-ordinal current-stage calculation) — for a true one-off, a
native SQL question on its own is fine, just say why it isn't a Model.

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
   available, say so and move to the next recommendation instead of forcing
   something with the wrong data.

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

This convention applies to every flow in this project — Transcript to
Insights and Requirements Intake both create individual cards directly in
the account's collection (neither flow assembles a dashboard).

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

- **After each card is created and verified** (`prompts/chart-generation.md`
  step 7): one `chart_created` entry per card.
  ```json
  {"timestamp": "2026-08-18T23:45:00Z", "type": "chart_created", "account": "662", "recommendation_rank": 1, "card_id": 70801, "name": "...", "chart_type": "bar", "collection_id": 24521}
  ```
  Add `"source": "transcript"` to entries from the Transcript to Insights
  flow, or `"source": "requirements_intake"` to entries from the
  Requirements Intake flow (and use `"requirement"` in place of `"insight"`
  in the `recommendations` array for that flow) so the two are
  distinguishable in `logs/history.jsonl`.

Any other genuinely useful event (e.g. an account that couldn't be located,
an analysis that had to be skipped for insufficient data) is fine to log too
with a descriptive `type` — `chart_created` isn't an exhaustive list, just
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
  of a comma-separated list. **Whether `deal_value` is split across those
  rows or repeated in full on each one is not consistent across accounts —
  verify it on this account's actual data before summing, never assume
  either way.** Observed on account 116830: a 5-collaborator "Equal Split"
  deal (`deal_split_percentage` 20 each) still carried the *full* deal value
  (4000) on every one of its 5 rows, not a 800/800/800/800/800 split — a
  bare `SUM(deal_value)` there would overcount that deal's revenue 5x.
  Check with a query like `SELECT id, deal_value, deal_split_percentage,
  collaborator_name FROM deals_<account> WHERE id IN (SELECT id FROM
  deals_<account> GROUP BY id HAVING COUNT(*) > 1) ORDER BY id` on a
  multi-collaborator deal for *this* account first. If it's split (values
  sum to the total), `SUM(deal_value)` is correct. If it's repeated (values
  are identical per id, as on 116830), aggregate to one row per id first —
  e.g. `SELECT id, MIN(deal_value) AS deal_value FROM deals_<account> GROUP
  BY id` — then `SUM` that. Either way, counting deals still needs
  `COUNT(DISTINCT id)`, never `COUNT(*)`.
- **Pitched Candidates**: a new row per status change — same pattern as
  Assignments.
- **Notes / Tasks / Meetings**: a new row per association (e.g. one note
  linked to multiple records can appear more than once under the same
  `id`) — dedupe before counting.

**Determining a candidate's current/furthest pipeline stage:** timestamps
between consecutive stage changes are often only seconds apart, so
`MAX(stage_date)` does **not** reliably identify the furthest-progressed
stage. Instead, rank stages by their actual business/funnel order — **ask
the user directly for this account's exact `hiring_stage` values and their
funnel order; never query the field's live values to discover them, and
never reuse another account's stage list** — with a `CASE` expression
assigning each stage an ordinal, giving any unrecognized value a large
fallback ordinal (e.g. 100), then take the row with `MAX(ordinal)` per
candidate-job pair as the current stage. Example shape (values are
illustrative — rebuild the mapping from the stage list and order the user
gave you for this account):

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

**There is currently no column encoding a stage's numeric order.** A
`hiring_stage_number`-style column that would make this directly
discoverable is planned but not yet added to the data. Until it exists,
never infer the funnel order from naming, alphabetical order, or
`MIN(stage_date)` — ask the user directly for the complete, exact list and
order of this account's `hiring_stage` values before building the ordinal
`CASE` mapping above; never query the field's live/cached values
(`mb field values`, `mb field summary`, or any `mb query`) to find or
confirm them instead of asking. Record the answer in
`references/metric-glossary.md` so it's asked once per account, not every
session. Once a `hiring_stage_number`-style column exists for an account,
that's schema metadata (a declared field, not a value sample) — prefer
reading the order from its presence/description over asking, but still
don't query its live values to reverse-engineer the mapping; ask the user
to confirm if the field's meaning isn't already documented.

**Stage-to-stage conversion ratios — avoid a naive ratio.** A straight
`COUNT(stage = B) / COUNT(stage = A)` between two funnel stages (e.g. "2nd
Interview" → "Final Interview") can be wrong even when both counts are
individually correct: data issues (a skipped stage, a manual correction) can
put an id in stage B without it ever having a row in stage A, so the
numerator isn't actually a subset of the denominator population. Build the
ratio as a double summarization instead:

1. First summarize: one row per id per stage it has ever reached (e.g.
   `COUNT(DISTINCT id)` grouped by `id`, `hiring_stage`).
2. Use that to isolate the correct denominator population: only the ids
   that actually reached the earlier stage (e.g. reached "2nd Interview" at
   least once).
3. Second summarize, restricted to that population: how many of those ids
   also reached the later stage (e.g. "Final Interview"). Divide by the
   count from step 2.

This is usually buildable entirely in the GUI/MBQL editor as a summarize on
top of a filtered summarize — it does not require native SQL. Example:
submitted-to-placed rate by company = (count of distinct ids per company
that reached "Placed") / (count of distinct ids per company that reached
"Submitted"), each side counted after first reducing to one row per id per
stage — never a raw `COUNT(*)` ratio. Apply the same technique to any
funnel-stage conversion metric, not just this example pair.

## Error handling — exact wording

- CLI unreachable: "Metabase CLI could not be accessed. Please verify the CLI
  installation and configuration."
- Auth failure: "Metabase authentication could not be verified. Please check
  the Metabase API key/configuration."
- Account not found: ask the user to verify the account number.
- Insufficient data for a specific analysis: name which analysis is affected
  and why, then continue with what the data does support.
- A requirement that can't be answered at all (missing data, or an
  assumption its definition rests on doesn't hold — e.g. "at-risk" meaning
  deals in a "Lost" stage the account has none of): follow
  `prompts/infeasible-requirement.md` — confirm the finding with the user
  first, then draft a customer-ready explanation, rather than just noting it
  and moving on.

## Style

Keep the conversation itself lightweight — this is the whole product. Don't
build scaffolding, servers, or files beyond what's in this repo unless the
user asks for something new. When in doubt about `mb` syntax, check
`--help`/`--help --json` rather than guessing.
