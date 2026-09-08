# Metric Glossary

Business-term definitions, confirmed with the user, mapped to the exact
column/filter that implements each one. Structural/definitional only — no
customer data.

**Status: not yet confirmed.** The questions below were generated from the
real columns discovered in `references/schema-map.md` (account 662) — answer
inline, or say "still deciding" per term and it stays open. Once answered,
this file gets rewritten as definitions instead of open questions, and
`prompts/requirements-intake.md` checks it before falling back to asking the
user mid-conversation.

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

## Open questions

1. **"Active candidate"** — which column/value defines this?
   `candidates.employment_status`? A recent-activity window on
   `last_communication_on`? Something else? (Note: exact `employment_status`
   values are account-specific — not yet confirmed for any account.)

2. **"Placed" / "Closed" (a hire happened)** — is this
   `assign_job_candidate.hiring_stage` reaching a specific value (e.g.
   "Placed")? If so, what's this account's exact stage name, and where does
   it fall in the funnel order (needed for the stage-ordinal `CASE` ranking
   per CLAUDE.md)? Since `hiring_stage_date` timestamps can be seconds apart,
   the stage order must come from you, not be inferred.

3. **"Call outcome" categories** — `call_logs.call_type_label` looks like
   the candidate column, but what are the actual outcome categories this
   account uses (e.g. Connected / No Answer / Voicemail), and does
   "duration > 1 minute" / "> 2 minutes" (seen in past requirements, see
   `logs/history.jsonl` account 98861) mean `duration_in_seconds` thresholds
   at 60 / 120?

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
   names and their **funnel order** must come from you directly, account by
   account — never from querying the field's live values. For account 662
   specifically (if you want its charts to use this glossary): what is the
   complete list of its `hiring_stage` values, in real funnel order?

7. **Term/value mismatches** — when a requirement uses wording that doesn't
   exactly match a value already confirmed here or in the schema (e.g. a
   requirement says "Internal Review Required" but no confirmed stage list
   has that exact name), the fix is to ask you which real value it maps to
   — never to query the field live to check what actually exists. Log the
   confirmed mapping here once you answer, so the same mismatch doesn't get
   re-asked next time.


**Term mappings (this account only):**
- "Sent to the client" / "Send to the client" → `hiring_stage = 'Send to the client'` (exact literal, stage 7)
- "Internal Review Required" → `hiring_stage = 'Internal Review'` (stage 31) — wording doesn't match exactly, confirmed by user
- "Submitted - Not Yet Presented" → no matching stage; user said to ignore/drop this condition when it comes up
- "Open positions" → `job_status_label = 'Open'`
- "User who set the status" (on `assign_job_candidate_53181`) → `updated_by` (not `assigned_by`)
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
