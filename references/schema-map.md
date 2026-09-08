# Schema Map — Recruit CRM on Starrocks (db id `13371569`)

Structural reference only — table/column names, types, keys, grain, and
known quirks. **No customer data (row values, names, numbers) is stored
here** — only metadata pulled via `mb table fields` / `mb table get`, which
is metadata about the schema, not the records themselves.

Harvested from account **662** (`Data Team WIP` collection 24521) on
2026-09-06, chosen because it already has all 12 core tables and confirmed
prior chart-building activity (see `logs/history.jsonl`). The 12-table shape
below is expected to hold for **every** account — verify with `mb search
<name>_<account> --models table --db-id 13371569` before assuming a table
exists for a new one; a couple of tables (Pitched Candidates, Teams) may not
apply to every account depending on which Recruit CRM modules the client
uses.

Every table is named `<EntityName>_<account_number>` physically (e.g.
`companies_662`), even though `mb search`/`table get` surface a generic
`display_name` like "Companies" — always confirm `db_id: 13371569` (never
the legacy Redshift `13371338`) before trusting a match, per CLAUDE.md.

## How to use this file

1. Check here first for a requirement involving one of these 12 entities —
   table shape, join path, and known gotchas are already resolved.
2. **Custom fields (suffixed `(cf)`) are NOT documented here** — they vary
   per account (see "Custom fields" section below). Discover them per
   account with `mb table fields <id>` scoped to that account's table,
   every time a requirement needs one.
3. If a requirement needs a column not listed here at all (not core, not a
   `(cf)` you've checked for), fall back to live discovery
   (`prompts/discovery.md`) — this file is not guaranteed exhaustive if the
   underlying Recruit CRM schema changes.
4. Row counts / cardinality are deliberately **not** included — getting them
   requires querying live data (`COUNT`), which this file's metadata-only
   harvest intentionally avoids. Pull them per-account, per-table, only when
   a specific chart's build actually needs to know (e.g. "is this dimension
   too sparse to chart").

## Duplicate-id tables (repeat from CLAUDE.md, confirmed again at the column level)

Multiple rows can share the same `id` — by design — on: **Deals,
Assign Job Candidate, Pitched Candidates, Meetings, Notes, Tasks.** Always
`COUNT(DISTINCT id)`, on every table, including the ones below with no known
duplicates (Companies, Contacts, Jobs, Candidates, Teams, Call Logs) — this
is a defensive default, not conditional.

---

## 1. Companies (`companies_<account>`)

**Grain:** one row per company. **PK:** `id`. **No duplicate ids.**

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK | |
| company_name / company_profile | Text | Company | |
| city | Text | City | |
| industry | Text | — | |
| website, facebook_profile, x_profile, linkedin_profile | Text | — | social/contact links |
| parent_company_name | Text | Company | |
| owner / owner_id | Text/Integer | Owner | one owner per company, no dedupe needed |
| off_limit_status_label, off_limit_reason, off_limit_created_on, off_limit_end_date | Text/DateTime | Category | "off-limits" flagging feature |
| open_jobs, closed_jobs, on_hold_jobs, cancelled_jobs | Integer | — | **pre-aggregated job counts already on the row** — no join to Jobs needed for basic open/closed/on-hold/cancelled counts by client |
| created_on / updated_on | DateTime | Creation/UpdatedTimestamp | |
| created_by / updated_by | Text | Author/Category/Recruiter | |

No custom (`cf`) fields on this account's Companies table.
No outbound FK columns — referenced by Contacts/Jobs/Deals/etc. via their own `join_for_companies_table`.

---

## 2. Contacts (`contacts_<account>`)

**Grain:** one row per contact. **PK:** `id`. **No duplicate ids.**

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK | |
| first_name / last_name / contact_name | Text | Name | |
| email_id, contact_number | Text | — | |
| city | Text | City | |
| designation | Text | — | |
| stage | Text | Category | contact-level pipeline stage (distinct from candidate hiring_stage) |
| last_sms_sent_on, last_email_sent_on, last_communication_on, last_linkedin_message_sent_on | DateTime | — | activity-recency fields |
| last_communication_method | Text | Category | |
| off_limit_status, off_limit_reason, off_limit_created_on, off_limit_end_date | — | Category | |
| owner_name / owner_id | Text/Integer | Owner | |
| creator_name / updator_name | Text | Author/Category | |
| join_for_companies_table | Integer | **FK → companies.id** | |
| created_on / updated_on | DateTime | Creation/UpdatedTimestamp | |

**Custom fields:** ~75 `(cf)`-suffixed columns on this account — mostly
one-off test fields (`testtext`, `qwerty`, `dropdown1`, etc.). Treat the
entire `(cf)` set as **account-specific**; never assume a `(cf)` name from
one account exists on another.

---

## 3. Jobs (`jobs_<account>`)

**Grain:** one row per job. **PK:** `id`. **No duplicate ids.**

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK | |
| job_name, job_code, description | Text | — | |
| city, state, country | Text | City/Country | |
| job_category, qualification, specialization, job_skill | Text | — | |
| no_of_openings | Integer | — | measure |
| min/max_experience_in_years | Integer | — | |
| job_type_label, salary_type_label, job_location_type | Text | Category | |
| annual_salary_min / annual_salary_max | Float | — | measure |
| job_status_label | Text | Category | **primary status dimension** (open/closed/on hold/cancelled — confirm exact values per account) |
| is_archived | Integer | — | boolean-ish flag |
| job_posting_date, job_closed_date, job_status_updated_on, created_on, updated_on | DateTime | — | |
| hiring_pipeline_name | Text | Category | which pipeline template this job uses |
| owner_name / owner_id | Text/Integer | Owner | |
| creator_name / updator_name | Text | Author/Category | |
| join_for_companies_table | Integer | **FK → companies.id** | |
| join_for_contacts_table | Integer | **FK → contacts.id** | |

**Custom fields:** ~45 `(cf)` columns on this account, similarly test-heavy
(`n5`, `dasda`, `metabase_test`, etc.) — account-specific, discover fresh.

---

## 4. Candidates (`candidates_<account>`)

**Grain:** one row per candidate. **PK:** `id`. **No duplicate ids.**

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK | |
| first_name/last_name/full_name | Text | Name | |
| email | Text | Email | |
| contact_number | Text | — | |
| date_of_birth / age | DateTime/BigInt | Birthdate | |
| gender | Text | Category | |
| city / country | Text | City/Country | |
| qualification, specialization, skills, language_skills | Text | — | |
| current_position, last_organisation | Text | — | |
| employment_status | Text | — | **key dimension** — e.g. employed/unemployed (confirm exact values per account) |
| willing_to_relocate | Integer | — | boolean-ish |
| work_exp_year / work_exp_month, relevant_experience | Integer | — | measures |
| notice_period_in_days | Integer | — | measure |
| current_salary / salary_expectation | Float | — | measures |
| salary_type, currency_country | Text | Category/Country | |
| source | Text | Source | sourcing channel — key dimension |
| last_sms_sent_on, last_email_sent_on, last_communication_on, last_linkedin_message_sent_on | DateTime | — | activity recency |
| off_limit_status, off_limit_reason, off_limit_created_on, off_limit_end_date | — | Category | |
| owner / owner_id | Text/Integer | Owner | |
| created_by / updated_by, created_on / updated_on | — | Author/timestamps | |
| join_for_contacts_table | Integer | **FK → contacts.id** | |
| join_for_companies_table | Integer | **FK → companies.id** | (linked contact's company) |

**Custom fields:** ~100 `(cf)` columns on this account — by far the most
custom-field bloat of any table here, almost entirely one-off/test fields.
**Always treat Candidates' custom fields as fully account-specific** —
discover live per account, never assume from this reference.

---

## 5. Assign Job Candidate (`assign_job_candidate_<account>`) — the hiring-stage pipeline table

**Grain:** one row per **candidate-job pair per hiring-stage event.** `id`
is unique per pair, **not** per row — expect duplicate ids (new row each
time the pair moves to a new stage).

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK (per pair) | duplicate rows expected |
| hiring_stage | Text | Category | **no ordinal column exists** — ask the user for this account's real stage order before building a `CASE` ranking (CLAUDE.md) |
| hiring_stage_date | DateTime | — | do **not** use `MAX()` to find current stage — stage changes can be seconds apart |
| joining_date | DateTime | JoinTimestamp | |
| job_status_label, job_city | Text | Category | copied from Jobs at assignment time |
| candidate_full_name, candidate_city, candidate_country | Text | — | copied from Candidates |
| employment_status, salary_type, currency_country, current_salary, salary_expectation, willing_to_relocate, notice_period_in_days | — | — | copied from Candidates at assignment time — **may drift from the live Candidates row over time** |
| source | Text | Source | |
| assigned_by | Text | Category | |
| share | Integer | — | |
| remark | Text | — | |
| job_owner_id / job_owner_name, candidate_owner_id / candidate_owner_name | — | Owner | **pair-level, repeated on every hiring-stage row** — dedupe on `id` before aggregating counts/values by owner |
| client_name, company_name, company_website, company_contact_name | — | Company | |
| created_on, job_created_on | DateTime | Creation | |
| updated_by / updated_on | — | — | |
| join_for_jobs_table | Integer | **FK → jobs.id** | |
| join_for_candidates_table | Integer | **FK → candidates.id** | |
| join_for_companies_table | Integer | **FK → companies.id** | |
| join_for_contacts_table | Integer | **FK → contacts.id** | |

**Custom fields:** 4 `(cf)` columns on this account (`field_on_04`, `abc`,
`job_specific_note`, `number_custom_field`) — light custom-field usage here
relative to Candidates/Jobs/Contacts.

---

## 6. Deals (`deals_<account>`)

**Grain:** one row per **deal-collaborator.** `id` is unique per deal, not
per row — duplicate ids expected whenever a deal has >1 collaborator.

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK (per deal) | duplicate rows expected |
| deal_name, deal_stage, deal_type | Text | Category | |
| deal_value | Decimal | — | **collaborator's split, not the deal total on this row** — `SUM(deal_value)` grouped by `id` gives the deal total **only if this account splits it**; verify per CLAUDE.md ("Deals" data-model note) before trusting a bare `SUM` |
| weighted_deal_value | Decimal | — | |
| deal_split_percentage | Float | Share | should sum to 100% across an id's rows |
| split_type | Text | Category | |
| collaborator_name | Text | — | this row's collaborator |
| owner_name / owner_id | — | Owner | **deal-level, repeated across every collaborator row** — dedupe on `id` before aggregating by owner |
| candidate_name, company_name, job_name | Text | — | denormalized from the joined entities |
| close_date, created_on, updated_on | DateTime | — | |
| creator_name / updator_name | Text | Author/Category | |
| is_archived | Integer | — | |
| is_owner_active | Integer | — | |
| join_for_candidates_table | Integer | **FK → candidates.id** | |
| join_for_companies_table | Integer | **FK → companies.id** | |
| join_for_jobs_table | Integer | **FK → jobs.id** | |

**Custom fields:** ~55 `(cf)` columns on this account, heavily test-junk
(long garbage-string field names present — a sign this account's Deals
custom fields are not representative of a real client's naming).

---

## 7. Call Logs (`call_logs_<account>`)

**Grain:** one row per call. **PK:** `id`. **No duplicate ids.**

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK | |
| call_id | Text | — | external call-system id |
| call_type / call_type_label | Text | Category | **call outcome/type dimension** — confirm exact label set per account before building a "call outcome" chart |
| related_type | Text | Category | which entity this call is tied to: Contact / Candidate / Company |
| call_to, call_from_name, candidate/contact_name, related_company_name, related_contact_profile | Text | — | denormalized display fields |
| call_notes | Text | — | |
| duration_in_seconds | Integer | Duration | measure |
| currency / cost_in_currency | Text/Float | Cost | measure |
| created_on, started_on, updated_on | DateTime | — | |
| created_by_id | Integer | Author | |
| contact_owner_id, candidate_owner_id, company_owner_id | Integer | Owner | **only one of these three is populated per row**, matching `related_type` — not tied to a `join_for_*` column directly |
| join_for_candidates_table | Integer | **FK → candidates.id** | |
| join_for_companies_table | Integer | **FK → companies.id** | |
| join_for_contacts_table | Integer | **FK → contacts.id** | |

No custom (`cf`) fields on this account's Call Logs table.

---

## 8. Meetings / 9. Notes / 10. Tasks (`meetings_<account>`, `notes_<account>`, `tasks_<account>`)

These three share one shape — documented together, differences noted.

**Grain:** one row per **{meeting|note|task}–association pair.** `id` is
unique per meeting/note/task, not per row — duplicate ids expected whenever
the same item is linked to more than one record.

**⚠️ Two different "related to" concepts, at two different scopes — do not
conflate them:**
- `related_to_name` / `related_to_type` — the item's **primary** association
  (the one record chosen as "Related To" on the form). **Item-level,
  identical on every row of the same item** — always the same value no
  matter how many rows the item has.
- `entity_type` + `join_for_entity_type` — **the per-row association**, and
  it covers *both* the primary association and every **secondary**
  association (anything the item is additionally linked/tagged to).
  `entity_type` is one of `candidate` / `company` / `contact` / `job` /
  `deals`; `join_for_entity_type` holds that record's id. **Always join on
  both together** (`entity_type = 'candidate' AND join_for_entity_type =
  candidates_<account>.id`) — ids are not unique across entity tables, so
  joining on `join_for_entity_type` alone can match the wrong table. In
  Metabase's GUI builder this needs a custom expression for the
  `entity_type = '<value>'` side.

  **Example:** a note whose primary "Related To" is candidate John, with
  secondary associations to one other candidate (Robert), one contact, and
  one job. That note has **4 rows**: `related_to_type` reads `candidate` on
  all 4 (John, the primary, never changes) — `entity_type` varies per row:
  2 rows `candidate` (John's own row and Robert's), 1 row `contact`, 1 row
  `job`. Count/group by `entity_type` (+ `join_for_entity_type`) to get
  real per-association numbers; `related_to_type` alone would say
  "candidate" on all 4 and hide the contact/job associations entirely.

- **Ignore `join_for_contacts_table` / `join_for_companies_table` /
  `join_for_jobs_table` / `join_for_candidates_table` / `join_for_deals_table`
  on these three tables** — not the join path; these carry no FK metadata
  and are slated for removal. `entity_type` + `join_for_entity_type` is the
  only association mechanism to use, for both primary and secondary.

| Column | Type | Notes |
|---|---|---|
| id | Integer | PK per item, duplicate rows expected — `COUNT(DISTINCT id)` |
| owner_name | Text | the item's own owner (meeting/note/task owner) — not the related record's owner |
| created_by / updated_by | Text | |
| contact_owner_id, candidate_owner_id, company_owner_id, job_owner_id, deal_owner_id, activity_owner_id | Integer | **item-level, repeated on every row** — only the one matching `related_to_type` is populated |

Type-specific columns:
- **Meetings:** `meeting_type`, `meeting_title`, `meeting_description`, `meeting_place`, `meeting_created_at`, `meeting_starts_at`, `meeting_ends_at`.
- **Notes:** `note_label`, `note_description`, `note_created_at`, `owner_id`.
- **Tasks:** `task_title`, `task_type_label`, `task_description`, `task_status`, `collaborators`, `task_created_at`, `task_starts_at`, `task_ends_at`.

No custom (`cf`) fields observed on any of these three tables for this account.

---

## 11. Pitched Candidates (`pitched_candidates_<account>`)

**Grain:** one row per **status-history entry for a pitch.** `id` is unique
per pitch, not per row — duplicate ids expected whenever a pitch's status
changes.

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK (per pitch) | duplicate rows expected |
| pitched_candidate_name, pitched_to_contact_name, pitched_to_company_name | Text | — | denormalized |
| status | Text | Category | pitch status — confirm this account's value set before charting |
| pitched_by | Text | Category | |
| pitched_on | DateTime | — | when originally pitched |
| candidate_owner_id, contact_owner_id | Integer | Owner | |
| join_for_contacts_table | Integer | **FK → contacts.id** | |
| join_for_candidates_table | Integer | **FK → candidates.id** | |
| join_for_companies_table | Integer | **FK → companies.id** | |

No custom (`cf`) fields on this account's Pitched Candidates table. Note:
not guaranteed to exist on every account — verify first (this is the
"Pitched Candidates" module, may not be enabled everywhere).

---

## 12. Teams (`teams_<account>`) — Recruiters/Users

**Grain:** one row per team member. **PK:** `id`. **No duplicate ids.** Very
small/narrow table — 5 columns total, no custom fields.

| Column | Type | Semantic type | Notes |
|---|---|---|---|
| id | Integer | PK | |
| team_member | Text | — | name |
| team_member_role | Text | Category | |
| teams | Text | Category | **comma-separated list, not a single value** — a member on more than one team has all their team names in this one field joined by commas (e.g. `"Sales, Recruiting"`). Don't `GROUP BY teams` directly expecting one team per row — split/unnest on the comma first if a chart needs a true per-team breakdown. |
| is_user_active | Integer | — | active/inactive flag |

No declared FK columns — other tables reference a user by `owner_id`/
`owner_name` (loose reference, not a declared `fk_target_field_id`) rather
than a formal FK to this table. Confirm the join column by id/name matching
if a chart needs to join back to Teams.

---

## Custom fields — always account-specific

Every table above except Companies, Call Logs, Meetings, Notes, Tasks,
Pitched Candidates, and Teams carries a long tail of `(cf)`-suffixed custom
fields on this account (Contacts ~75, Jobs ~45, Candidates ~100, Deals ~55,
Assign Job Candidate 4). On account 662 these are overwhelmingly test/junk
fields (`qwerty`, `testtext`, `dasdadad`, garbage-string names) — **this
account is not a representative sample of what a real client's custom
fields look like,** only proof that the volume and shape vary wildly and
must never be assumed from one account to the next.

**Rule: never carry a `(cf)` field name forward from this file or from one
account to another.** Every requirement that needs a custom field must
resolve it live, per account:

```bash
mb table fields <table-id> --profile <profile> --json | jq '.data[] | select(.name | endswith("(cf)"))'
```
