# Requirements Intake

Goal: build charts from requirements the user states directly (not
discovered via insight-analysis, not extracted from a transcript) — check
known reference material and canonical patterns first, ask only genuinely
necessary clarifying questions, and never create anything before the user
confirms.

## Intake

1. Ask for the account number (same convention as the other flows).
2. Ask the user to paste their requirements — accept any format: a single
   ask, a numbered list, a pasted client doc listing several asks. Encourage
   (but don't require) this shape per requirement: metric / grain / filter /
   time range / why.

## Resolving each requirement

For each requirement, in this order:

1. **Check for a known pattern first.** If `references/canonical-patterns.md`
   exists in this repo, check it for a chart shape that matches before doing
   anything else. A match tells you the tables/join/grain/chart type
   directly — treat rediscovery as unnecessary in that case.
2. **Check reference material next.** If `references/schema-map.md` and/or
   `references/metric-glossary.md` exist, use them to resolve table/column
   choices and business-term definitions (e.g. "active candidate," "placed,"
   "assigned," "this month") before falling back to live inspection.
3. **Fall back to live discovery** exactly as `prompts/discovery.md`
   describes whenever no reference file covers what's needed —
   `references/schema-map.md` and `references/metric-glossary.md` exist
   today; `references/canonical-patterns.md` does not yet (see
   `prompts/metabase_skill_improvement.md` for how to build it). A
   requirement not covered by any reference file goes through this
   fallback at full rigor, same as any other discovery.
4. **Group by shared entity/model** when several requirements arrive at
   once — work out shared query/model logic once rather than per chart.
5. Check for duplicates the same way as CLAUDE.md's "Avoiding duplicate
   charts" — flag a match instead of silently recreating it.

## When to actually ask a question

Ask a narrow, specific clarifying question only when a requirement is
genuinely ambiguous in a way that changes the query — never as a general
hedge. Same bar as `prompts/transcript-insights.md`'s "Follow-up questions"
section: name the actual fork ("by assignment created date or hiring stage
date?"), never ask a vague "can you clarify?" If nothing is genuinely
ambiguous, don't ask anything.

**A requirement's wording not exactly matching a known value is one of
these forks — resolve it by asking, never by querying live data to check.**
e.g. the user writes "Internal Review Required" but the confirmed stage
list (schema-map.md / metric-glossary.md) has no such value: ask directly
("did you mean the 'Internal Review' stage, or something else?") rather
than running `mb field values`/`mb query` to see what's actually there. Once
confirmed, record the mapping in `references/metric-glossary.md` so the same
term doesn't get re-asked.

If the account's data can't actually support a requirement — missing
table/field, the concept doesn't exist for this account, or an assumption
the requirement's definition rests on doesn't hold in the real data — follow
`prompts/infeasible-requirement.md`: confirm the finding with the user
first, then draft a customer-ready explanation. Don't fabricate or
approximate it, and don't silently drop it either.

## Output format — numbered list

Present every requirement that resolved to a buildable chart as a numbered
list, in the order the user listed them:

```
### Chart #<n>

**Requirement**
<the user's ask, quoted or closely paraphrased>

**Recommended Chart**
<chart title>

**Chart Type**
<bar / line / funnel / stacked bar / scatter / table / KPI / area / combo>

**Why This Chart**
<why this visualization fits the data/ask>

**Recommended Metrics**
<fields/aggregations actually discovered>

**Recommended Filters (If Any)**
<only include this field at all if a filter is genuinely useful; omit it
entirely otherwise>

**Open Question (If Any)**
<omit entirely unless there's a genuine fork per "When to actually ask a
question" above>
```

After the numbered list, call out separately (not numbered as a chart) any
requirement that couldn't be built, and why.

## Confirm, then build

Same confirm-before-create gate as `prompts/chart-generation.md` — ask which
of the numbered charts to actually create ("create all" creates every one
presented). Resolve any open questions and get an answer before creating a
card that had one — don't build on an assumed interpretation. Build and
verify each exactly per `prompts/chart-generation.md`, including its
validation step (cross-check the result against a raw/independent number
before naming and saving it).

Cards land under "Data Team WIP" using the account-collection convention
described in CLAUDE.md "Where created charts live" — individual cards
directly in the account's collection, not a sub-collection, and **not**
assembled into a dashboard.

## Logging

Log per CLAUDE.md "History log" — a `recommendations_presented` entry after
presenting the numbered list, and one `chart_created` entry per card
actually created. Add `"source": "requirements_intake"` to both. In the
`recommendations` array, use `"requirement"` in place of `"insight"` — the
rest of the shape matches CLAUDE.md's example.
