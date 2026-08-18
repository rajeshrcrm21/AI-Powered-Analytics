# Discovery

Goal: build an accurate map of what data actually exists for this account
before analyzing or recommending anything. Everything here is done via `mb`.

## 1. Locate the account

See CLAUDE.md "Locating the account's data". Confirm you know *which*
database (and, if relevant, which schema or tenant filter) corresponds to the
account number the user gave you before going further. If you can't confirm
it confidently, ask rather than guess.

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

For each, note:

- Record count (query `count(*)` or check any summary metadata available)
- Key dimensions: status/stage fields, owner/recruiter fields, date fields,
  category-like fields
- Key measures: anything summable/averageable (amounts, durations, counts)
- Foreign keys / relationships to other relevant tables
- Field semantic types already set (helps spot dates, FKs, categories fast)

## 4. Check field-level data shape

Where a field looks important (status, stage, recruiter, date), sanity-check
its actual values before trusting it as a dimension:

```bash
mb field values <field-id> --json     # cached distinct values
mb field summary <field-id> --json    # live cardinality: count vs distincts
```

Watch for: a "status" field with only one distinct value (useless as a
dimension), a recruiter/owner field that's mostly null, a date field with
implausible values (e.g., far-future or epoch-zero dates).

## 5. Check existing analytics

```bash
mb search <account-related term> --models card,dashboard --limit 20 --json
```

Note what already exists so recommendations don't duplicate it (see
CLAUDE.md "Avoiding duplicate charts").

## 5b. Check for duplicate-ID tables

Per CLAUDE.md's "Recruit CRM / Metabase data model" section, Deals,
Assignments, Pitched Candidates, Notes, Tasks, Meetings, and sometimes Call
Logs legitimately contain repeated `id` values by design (one row per stage/
status/association change) — Candidates, Contacts, Jobs, Teams, and
Companies do not. Confirm this holds for the tables in play here with a
quick check:

```sql
SELECT COUNT(*) AS rows, COUNT(DISTINCT id) AS distinct_ids FROM <table>
```

If `rows > distinct_ids` on one of the expected tables, that's normal —
carry `COUNT(DISTINCT id)` forward into analysis, not `COUNT(*)`. If it
happens on a table expected to have unique ids, treat that as a real data
quality flag instead.

## 6. Summarize before moving on

Before starting analysis, produce (internally, or briefly to the user if
useful) a short map of: which entities exist, which are usable, which are
too sparse/dirty to trust, and what relationships connect them. This feeds
directly into `prompts/analysis.md`.
