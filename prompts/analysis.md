# Analysis

Goal: turn the discovery map into candidate business insights, grounded in
data you actually queried through `mb` — not assumptions about what recruiting
data usually looks like.

## Querying

Use `mb query` (MBQL preferred; load the `mbql` skill before authoring
non-trivial queries) to run ad-hoc aggregations against the discovered
tables. Use `--dry-run` to validate before running. For anything not
expressible in MBQL, fall back to native SQL (load the `native-sql` skill)
using only fields confirmed to exist.

**Always use `COUNT(DISTINCT id)` for counts, on every entity, never
`COUNT(*)`** — a defensive default per CLAUDE.md's duplicate-ID rules, not
just something to remember for Deals, Assignments, Pitched Candidates, and
Notes/Tasks/Meetings (the entities that actually have duplicate-id rows
today). Remember Deal *value* is already split across duplicate-id rows (so
`SUM()` is correct as-is for value, but not for counting deals — that still
needs `COUNT(DISTINCT id)`). A candidate's **latest** hiring stage and their
**maximum/farthest** hiring stage are different questions — per CLAUDE.md,
"latest" is the most recent `hiring_stage` value by `MAX(stage_date)` (no
CASE ranking), while "maximum/farthest" needs the stage-ordinal `CASE` +
`MAX(ordinal)` technique rather than trusting stage-change timestamps, which
are often only seconds apart and don't reliably reflect funnel order. Pick
the one the question actually calls for.

## Example angles to investigate (not a checklist — pursue what the data supports)

**Hiring funnel** — volumes at each stage (applied/screened/interview/
offer/placed, or whatever stages this account actually uses); where the
biggest drop-offs are; how conversion trends over time.

**Recruiter performance** — placement conversion and workload by recruiter;
which recruiters are notably above/below the team; whether differences hold
up given sample size (a recruiter with 3 jobs isn't comparable to one with
80).

**Job activity** — open jobs with little/no candidate activity; jobs open
unusually long; jobs with many candidates but zero placements; stalled jobs.

**Client/company activity** — clients with multiple open jobs but no recent
placements; clients trending down in activity; top clients by placements;
high-opportunity, low-engagement clients.

**Candidate activity** — activity trends by day/week/month; funnel
progression; unexpected drop points.

**Time trends** — placements, job openings, candidate activity, and
conversion rates over time — up, down, or flat.

Only pursue an angle where the required entities/fields actually exist and
passed the data-quality gate below. A thin or dirty account might only
support 2-3 of these — that's fine; don't force the rest.

## Data quality gate — apply before treating anything as a candidate insight

Exclude (and note internally why) any pattern that rests on:

- Null/empty rate high enough to distort the metric (e.g., most records
  missing the dimension being sliced by)
- Very small record counts (a handful of records dressed up as a trend)
- Duplicate records inflating counts
- Invalid or implausible dates
- A status/stage field with near-zero variance (can't show a distribution)
- Insufficient history to call something a "trend" (e.g., one month of data)

If an insight is directionally interesting but the underlying data is shaky,
either downgrade its rank (see `prompts/recommendation.md`) or drop it
entirely if presenting it would mislead. Say which, and why, when relevant.

## Output of this stage

A list of candidate insights, each with: the actual finding (with real
numbers/patterns from the query results), which entities/fields it depends
on, and a rough data-quality confidence. This feeds `prompts/recommendation.md`.
