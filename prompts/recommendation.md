# Recommendation

Goal: rank candidate insights from `prompts/analysis.md` and present exactly
N of them (the count the user requested) in a consistent, decision-useful
format.

## Ranking criteria

Weigh each candidate insight on:

1. Business impact — does it point at money, time, or placements at stake?
2. Strength of the observed pattern — clear signal vs. marginal/noisy
3. Actionability — can someone actually do something about it?
4. Data reliability — did it pass the data-quality gate cleanly, or barely?
5. Relevance to recruitment operations specifically
6. Uniqueness vs. existing Metabase content (see CLAUDE.md "Avoiding
   duplicate charts")
7. How clearly a chart can communicate it

A specific, actionable, well-evidenced finding ("14 open jobs have had zero
candidate activity in 30+ days") outranks a generic-but-common chart
("candidates by month") even though the latter is more familiar. Prefer the
former.

If fewer than N insights survive the data-quality gate and ranking with
genuine confidence, say so explicitly and return fewer rather than padding
with weak filler.

## Output format — use this exact structure per recommendation

```
### Recommendation #<n>

**Recommended Chart**
<chart title>

**Chart Type**
<bar / line / funnel / stacked bar / scatter / table / KPI / area / combo>

**Insight**
<the actual finding from the customer's data>

**Business Question**
<the question this chart answers>

**Why This Chart**
<why this visualization fits the data/insight>

**Recommended Metrics**
<fields/aggregations actually discovered>

**Recommended Filters**
<only filters that are genuinely useful — date, recruiter, job, company,
candidate status, job status, etc.>

**Data Evidence**
<the real pattern/numbers observed via mb query — never fabricated>
```

Number recommendations best-first (Recommendation #1 = highest ranked).

## Logging

Immediately after presenting the recommendations to the user, append one
`recommendations_presented` entry to `logs/history.jsonl` (see CLAUDE.md
"History log" for the exact schema and how to get the timestamp). Include
every recommendation actually presented, even if fewer than N.
