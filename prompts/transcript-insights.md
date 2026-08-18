# Transcript to Insights

Goal: turn a raw client meeting transcript (call recording transcript or
notetaker output) into chart recommendations — grounded in that account's
real data, never invented from the transcript alone.

## Reading the transcript

Accept whatever the user pastes as-is — a raw call transcript, a notetaker
summary, informal or messy text, multiple speakers, timestamps, filler words.
Don't ask them to clean it up first. Read the whole thing before extracting
anything.

Pull out every place the client expresses (explicitly or implicitly) a wish
to measure, track, see, or report on something — e.g. "we want to see how
each recruiter is doing," "can we get a view of deals closing," "I'd like to
know which clients have gone quiet." Informal language is normal; translate
the underlying analytics need, don't require the client to have spoken in
chart terms.

If a request is too vague to map to a specific chart (e.g. "better visibility
into the pipeline" with no further detail), don't guess a specific
interpretation — note it as an open question to ask the user about rather
than picking one arbitrarily.

## Grounding requirements in real data

For each extracted requirement:

1. Locate the account (see CLAUDE.md "Locating the account's data") and run
   discovery per `prompts/discovery.md` against the entities the requirement
   implies — same rigor as the Recommendation Engine flow, not a shortcut.
2. Check whether the account's actual tables/fields can support the request
   (per CLAUDE.md's data model rules — duplicate-ID handling, current-stage
   determination, etc. all still apply here).
3. If the data supports it, build the chart candidate the same way
   `prompts/analysis.md` treats a candidate insight — grounded in a real
   query, not a guess at what the numbers probably look like.
4. If the account's data **cannot** support a requirement (missing
   table/field, or the concept doesn't exist for this account), do not
   fabricate or approximate it. Say so explicitly and specifically (which
   requirement, why it can't be built) instead of silently dropping it.

Before finalizing, check for duplicates the same way as CLAUDE.md's
"Avoiding duplicate charts" — a request that matches something that already
exists should be flagged as such, not recreated blindly, unless the new
version is materially better or answers something genuinely different.

## Output format — numbered list

Present every requirement that resolved to a real, buildable chart as a
numbered list, in the order they came up in the transcript. Reuse
`prompts/recommendation.md`'s per-item structure, with one addition at the
top of each item:

```
### Chart #<n>

**Client's Ask**
<what the client actually said or asked for, quoted or closely paraphrased>

**Insight**
<what this chart will actually show, grounded in the real data>

**Recommended Chart**
<chart title>

**Chart Type**
<bar / line / funnel / stacked bar / scatter / table / KPI / area / combo>

**Business Question**
<the question this chart answers>

**Why This Chart**
<why this visualization fits the data/insight>

**Recommended Dimensions**
<fields actually discovered>

**Recommended Metrics**
<fields/aggregations actually discovered>

**Recommended Filters**
<only filters that are genuinely useful>

**Data Evidence**
<the real pattern/numbers observed via mb query — never fabricated>
```

After the numbered list, call out separately (not numbered as a chart):
- Any requirement that couldn't be built, and why.
- Any requirement too vague to interpret, framed as a question back to the
  user.

## Creating confirmed charts

Same confirm-before-create gate as `prompts/chart-generation.md` — ask which
of the numbered charts to actually create ("create all" creates every one
presented). Build and verify each exactly per `prompts/chart-generation.md`.

Cards land under "Data Team WIP" using the same account-collection
convention as the Recommendation Engine flow (CLAUDE.md "Where created
charts live") — individual cards directly in the account's collection, not a
sub-collection, and **not** assembled into a dashboard. Dashboard assembly
for this flow is future scope.

## Logging

Log per CLAUDE.md "History log" — a `recommendations_presented` entry after
presenting the numbered list, and one `chart_created` entry per card
actually created. Add `"source": "transcript"` to both so they're
distinguishable from Recommendation Engine entries in `logs/history.jsonl`.
