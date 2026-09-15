# Metric Glossary

Business-term definitions, confirmed with the user, mapped to the exact
column/filter that implements each one — kept **per account**. A mapping
confirmed for one account must never be assumed to hold for another (per
CLAUDE.md "Data discovery" and "Term/value mismatches" below); this file is
organized by account precisely so that rule is enforced by its structure,
not left to convention alone. Structural/definitional only — no customer
data.

**No answer here is ever obtained by querying live data, or by inferring it
from existing content.** Every value list, stage order, and term definition
below comes only from what the user confirms directly — never from
`mb field values`, `mb field summary`, `mb query` run to sample/check what's
actually in a column, **and never from reverse-engineering an existing
card's saved query** (a `CASE` expression's stage ordering, a filter's
literal values, etc. — see CLAUDE.md "Avoiding duplicate charts" and
`prompts/discovery.md` section 5). An old card that already encodes a
plausible-looking answer is still not a substitute for asking. If a term is
still unconfirmed when a chart needs it, the flow asks the user in-session,
with no priors, rather than checking the data — or existing content — itself
(see `prompts/discovery.md` section 4).

**Every confirmed answer gets written here immediately — in the same turn
it's confirmed, before moving on to the next question or building the
chart.** Holding a confirmed answer in conversation context to write back
later (or never) is exactly how "ask once per account" quietly turns into
"ask every time" — see `prompts/discovery.md` section 4, `prompts/
chart-generation.md`'s currency step, and `prompts/requirements-intake.md`'s
"When to actually ask a question".

## How this file is organized

- **Open questions (template)** — the standing list of business terms that
  typically need a confirmed answer before they can be used in a chart,
  for *any* account. This list is not itself account-specific; it's what to
  walk through the first time one of these terms comes up for a given
  account, and it stays here even after some accounts have answered it.
- **Account sections** (`## Account <number>`) — one per account this
  project has actually confirmed answers for, holding that account's own
  confirmed term mappings and any other per-account facts (hiring-stage
  order, currency, etc.). Before resolving a business term for account X,
  check X's own section first; never reuse another account's section, and
  never create a new account's section by copying an existing one's answers
  forward.
- **Unattributed** — mappings recorded before this file was organized by
  account, with no account number recoverable from how they were written.
  They are not usable for any specific account as-is — see that section.

## Open questions (template)

1. **"Active candidate"** — which column/value defines this?
   `candidates.employment_status`? A recent-activity window on
   `last_communication_on`? Something else? (Note: exact `employment_status`
   values are account-specific — confirm fresh per account.)

2. **"Placed" / "Closed" (a hire happened)** — is this
   `assign_job_candidate.hiring_stage` reaching a specific value (e.g.
   "Placed")? If so, what's this account's exact stage name, and where does
   it fall in the funnel order (needed for the stage-ordinal `CASE` ranking
   per CLAUDE.md)? Since `hiring_stage_date` timestamps can be seconds apart,
   the stage order must come from the user, not be inferred.

3. **"Call outcome" categories** — `call_logs.call_type_label` looks like
   the candidate column, but what are the actual outcome categories this
   account uses (e.g. Connected / No Answer / Voicemail), and does
   "duration > 1 minute" / "> 2 minutes" (seen in past requirements) mean
   `duration_in_seconds` thresholds at 60 / 120?

4. **"Assigned"** (a candidate assigned to a job) — does this mean a row
   simply exists in `assign_job_candidate` for that pair (any stage), or
   specifically reaching a named early stage (e.g. "Assigned" as a literal
   `hiring_stage` value)? `assign_job_candidate.assigned_by` also exists —
   is that relevant to the definition, or just metadata about who did it?

5. **"This month" / "recent"** — when a requirement doesn't specify a date
   column, which one resolves it by default? Candidates for "recent
   activity": `created_on`, `updated_on`, `last_communication_on` (candidates
   /contacts), `hiring_stage_date` (pipeline), `created_on`/`started_on`
   (calls). Likely different per entity — confirm per entity rather than
   one blanket rule.

6. **Funnel/hiring-stage values and order** — per CLAUDE.md, there is
   currently no numeric-order column, so both the **exact list** of stage
   names and their **funnel order** must come from the user directly,
   account by account — never from querying the field's live values. What
   is the complete list of this account's `hiring_stage` values, in real
   funnel order?

7. **Term/value mismatches** — when a requirement uses wording that doesn't
   exactly match a value already confirmed here or in the schema (e.g. a
   requirement says "Internal Review Required" but no confirmed stage list
   has that exact name), the fix is to ask the user which real value it maps
   to — never to query the field live to check what actually exists. Log the
   confirmed mapping under this account's own section once answered, so the
   same mismatch doesn't get re-asked next time.

8. **Currency** — per CLAUDE.md "Value formatting", monetary fields
   (`deal_value`, `budget_allocated`, `cost_in_currency`, salary/package
   fields, etc.) must be chart-formatted with the right currency symbol, and
   that currency is never assumed. Which ISO 4217 currency code applies
   (e.g. USD, EUR, GBP, INR) for this account?

## Account sections

No account has a fully confirmed set of answers yet. Add a `## Account
<number>` section here the first time a term is confirmed for that account,
in this shape:

```markdown
## Account 662

**Confirmed term mappings:**
- "Open positions" → `job_status_label = 'Open'`

**Hiring-stage order:** (fill in once confirmed, per "Open questions" #6)

**Currency:** (fill in once confirmed, per "Open questions" #8)
```

## Unattributed (predates per-account structure — reconfirm before use)

These mappings were recorded before this file separated answers by account.
No account number is recoverable from how most of them were written, so
**they must not be assumed to apply to any specific account, including the
one a current session happens to be working on.** If a similar term comes
up for any account, ask the user fresh per "When to actually ask a
question" (`prompts/requirements-intake.md`) and record the confirmed
answer under that account's own section above — don't reuse one of these
entries as if it were already confirmed for that account.

- "Sent to the client" / "Send to the client" → `hiring_stage = 'Send to the client'` (exact literal, stage 7)
- "Internal Review Required" → `hiring_stage = 'Internal Review'` (stage 31) — wording doesn't match exactly, confirmed by user
- "Submitted - Not Yet Presented" → no matching stage; user said to ignore/drop this condition when it comes up
- "Open positions" → `job_status_label = 'Open'`
- "User who set the status" (on `assign_job_candidate_53181`, i.e. **account 53181** — the one entry here with a recoverable account number; move it to its own `## Account 53181` section once that account's other answers are confirmed) → `updated_by` (not `assigned_by`)
- "The manager" (in "positions not owned by the manager") → the candidate's owner field (`candidate_owner_name`); "not owned by the manager" = `job_owner_name <> candidate_owner_name` (position owner differs from the candidate's owner)

## How to answer

Reply inline, e.g.:

> 1. Active candidate = `employment_status` in ('Unemployed','Actively
>    Looking') OR `last_communication_on` within 90 days
> 2. Placed = hiring_stage = 'Placed', which is the last stage before
>    Rejected/Withdrawn in the funnel
> ...

Anything left unanswered stays an open question — `prompts/requirements-intake.md`
will still ask about it live the first time a requirement actually needs
that specific definition, per its "When to actually ask a question" rule
(never as a blanket upfront hedge).
