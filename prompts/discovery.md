# Discovery

Goal: build an accurate map of what data actually exists for this account —
tables, columns, types, relationships — **without ever reading the account's
underlying row data.** Everything here is metadata: what exists and what
shape it has, never what values are actually inside it. `references/schema-map.md`
already covers this for the 12 core entities; this file is the fallback for
whatever it doesn't cover (a new account, a table not yet documented, a
custom field).

**Hard rule for this file: no step below may execute a query that returns
row content, aggregates over row content, or samples a column's actual
values.** That means no `mb field values`, no `mb field summary`, no
`mb query` (dry-run is fine — it only validates shape, never executes), no
`SELECT count(*)`/`SELECT ... FROM` of any kind. If a step here used to
recommend one of those, it doesn't anymore — see "Where value/data
questions actually get resolved" below.

## 1. Locate the account

See CLAUDE.md "Locating the account's data". Confirm you know *which*
database (and, if relevant, which schema or tenant filter) corresponds to
the account number the user gave you before going further. If you can't
confirm it confidently, ask rather than guess. This is a metadata lookup
(`mb search`, `mb database get --include tables`, matching on table
`description`) — no data read.

## 2. Map the database

```bash
mb database get <db-id> --include tables --json
```

This gives a compact table map (id, name, schema, description). Skim names
for the Recruit CRM entities that matter for hiring analytics — do not assume
any of these exist; only the ones actually present are in play:

- Candidates
- Companies / Clients
- Contacts
- Jobs / Job requisitions
- Job assignments / pipeline stages / candidate-job links
- Placements
- Deals
- Notes
- Tasks
- Meetings
- Calls
- Recruiters / Users
- Any status/stage lookup tables

If the database has many tables, don't pull full metadata for all of them —
narrow first with `mb database schemas <db-id>` /
`mb database schema-tables <db-id> <schema>`, or `mb search <term> --models
table --db-id <db-id>` to find candidates by name.

## 3. Inspect relevant tables

For each table that looks relevant:

```bash
mb table fields <table-id> --json
```

For each, note (all of this is column-level metadata, not row content):

- Key dimensions: status/stage fields, owner/recruiter fields, date fields,
  category-like fields — identified by name/`semantic_type`/`description`,
  not by sampling what's actually stored in them
- Key measures: anything summable/averageable (amounts, durations, counts),
  again by type/name/description
- Foreign keys / relationships to other relevant tables
- Field semantic types already set (helps spot dates, FKs, categories fast)

Row counts and record volumes are **not** gathered at this stage — that
would require querying real data. If a chart's build later needs to know
whether a dimension is too sparse to trust, that's assessed at
`prompts/chart-generation.md`'s one validation step, not here.

## 4. Where value/data questions actually get resolved

A field's *name* and *type* are metadata (covered above). A field's actual
*contents* — which stage names exist, what a status label's real values
are, whether a specific category is present at all — are data, and this
project does not query for them during discovery. Resolve these instead:

1. **Check `references/metric-glossary.md` first** — confirmed business-term
   definitions (e.g. "active candidate," "placed," this account's
   `hiring_stage` order) live there once answered.
2. **If not covered there, ask the user directly.** This is exactly what
   CLAUDE.md's "When to actually ask a question" bar is for — a narrow,
   specific question naming the actual fork (e.g. "this account's real
   `hiring_stage` values — what's the exact list and order?", or "you said
   'Internal Review Required' — is that the same as this schema's
   `hiring_stage` category, or a different one?"). Never query the field's
   live values to check or guess instead of asking.
3. **If truly nothing else resolves it**, the query gets built anyway on the
   best available definition and validated once at build time
   (`prompts/chart-generation.md`) — that single, unavoidable run is where a
   wrong assumption or a missing category value actually surfaces (see
   `prompts/infeasible-requirement.md`), not a separate live probe during
   discovery.

Watch for structural (not data) red flags instead: a status/stage column
with a generic name suggesting it might be unused, an owner/recruiter field
that looks like a display-name duplicate of another column, a date column
whose name doesn't clearly say what event it marks. These are things to ask
about, not query for.

## 5. Check existing analytics

```bash
mb search <account-related term> --models card,dashboard --limit 20 --json
```

This searches card/dashboard *names*, not their data — note what already
exists so recommendations don't duplicate it (see CLAUDE.md "Avoiding
duplicate charts").

**This step is name/description-level only. Do not open a matched card's
`dataset_query` (`mb card get <id>`) to read its filter literals, `CASE`
expressions, or any other embedded business values (e.g. reverse-engineering
a hiring-stage order from an existing card that already ranks stages) — that
is the same problem as querying live field values by another route: it
produces a guessed value list to hand back to the user as "confirm this"
instead of asking them cleanly with no priors. An existing card's *name* can
tell you a duplicate exists; its *query body* is off-limits as a source for
resolving what a term means or what values/order it takes. That comes only
from the user (directly, or already confirmed in
`references/metric-glossary.md`) — never inferred from what an old card
happens to encode, however plausible it looks.**

## 5b. Duplicate-ID tables — known from CLAUDE.md, not verified live

Per CLAUDE.md's "Recruit CRM / Metabase data model" section, Deals,
Assignments (Assign Job Candidate), Pitched Candidates, and Notes/Tasks/
Meetings legitimately contain repeated `id` *values* by design — Candidates,
Contacts, Jobs, Teams, Companies, and Call Logs do not. Treat this as
standing knowledge, not something to confirm with a live
`COUNT(*)`/`COUNT(DISTINCT id)` check — that would be a data read this file
doesn't do. **Regardless, always carry `COUNT(DISTINCT id)` forward into any
query on any entity, never `COUNT(*)`** — a defensive default per CLAUDE.md,
true whether or not this specific table is known to have duplicates today.

If a table genuinely not covered by CLAUDE.md's list needs this determined
(e.g. a newly-discovered entity), ask the user rather than probing live data
to find out.

## 6. Summarize before moving on

Before starting analysis, produce (internally, or briefly to the user if
useful) a short map of: which entities exist, which are structurally usable
(core columns/relationships present), and what relationships connect them.
This is a structural summary, not a data-quality judgment — data-quality
concerns (sparse, dirty, thin) are for CLAUDE.md's "Data quality gate"
(thresholds in `config/analysis-config.md`), and even there they're assessed
at the one validation point in chart-generation, not by live-sampling during
discovery.
