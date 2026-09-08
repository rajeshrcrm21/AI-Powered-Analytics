# When a requirement can't be built

Applies wherever any flow finds that a requirement — stated directly, or
pulled from a transcript — can't be answered from the account's real data.
This covers more than a missing table/field:

- A required table/field genuinely doesn't exist for this account (a
  metadata fact, from `references/schema-map.md` or a live `mb table
  fields`/`mb search` check — no row data involved).
- The data is too thin or dirty to trust (see CLAUDE.md's "Data quality
  gate" section).
- **An assumption the requirement's definition rests on doesn't hold in this
  account's actual data** — e.g. "at-risk deals" defined as deals sitting in
  a "Lost" stage, but this account currently has zero deals in that stage.
  This is not a data-quality defect and not a reason to silently drop the
  requirement — the definition itself needs confirming, and the account
  genuinely may have no data matching it *right now*.

**How "what the real data shows instead" gets known, for the cases above
that involve row content (not just missing tables/fields):** this project
never runs a separate live probe during discovery/resolution to check a
guess. The only point any of these flows executes against real row data is
`prompts/chart-generation.md`'s one validation run, right before saving the
card — build the query on the best-confirmed definition, validate it once,
and if that run comes back empty, mismatched, or erroring on a category
that doesn't exist, *that* result is what gets reported here as "what was
found." Don't add a separate check earlier just to confirm a suspicion
sooner.

Never silently drop a requirement that hits one of these, and never
fabricate a workaround or approximate an answer. Handle it in two steps.

## Step 1 — confirm with the user first

Before drafting anything client-facing, tell the user (the person running
this session) what was found and ask for their read on it — don't skip
straight to a final explanation:

> For "\<requirement>", here's what I found: \<the specific thing checked —
> table/field looked for, or the exact assumption tested and what the real
> data shows instead>. Am I understanding this correctly, or do you have a
> different approach for defining/finding this?

Wait for their answer. They may confirm the gap is real, correct a wrong
assumption (e.g. the right definition actually uses a different stage or
field), or point at data this session hasn't checked yet. Only move to
Step 2 once this is resolved one way or the other — don't draft a
client-facing explanation off an unconfirmed guess.

## Step 2 — draft a customer-ready explanation

Once confirmed, draft a short, factual paragraph suitable to send to the
client as-is (e.g. in an email):

- Plain business language — no table/column names, no SQL, no internal
  jargon.
- State plainly whether the request is possible right now, and why or why
  not, grounded only in what was actually observed — never a fabricated
  number or guess.
- If it isn't possible today, say what would make it possible (e.g. "once
  deals start moving into a Lost stage, we can build this").

Present the draft to the user before it goes anywhere else — this project
never sends anything to a customer itself; it only prepares the text for the
user to review and send.
