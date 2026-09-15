# Analysis configuration

Defaults and knobs shared by this project's chart-building flow
(Requirements Intake). Adjust here rather than in CLAUDE.md if these need to
change per-deployment.

## Data quality defaults (CLAUDE.md "Data quality gate")

- Minimum record count to trust a distribution/trend as meaningful: judge in
  context, but treat anything under ~20 records as "too small to trust" for
  that specific slice, and say so rather than silently building the chart.
- Minimum history to call something a "trend": at least a few periods of the
  chosen granularity (e.g., 3+ months for a monthly trend) — a single data
  point is a fact, not a trend.

## Candidate entities (adapt to what actually exists per account)

Candidates, Companies/Clients, Contacts, Jobs, Job Assignments/Pipeline
Stages, Placements, Deals, Notes, Tasks, Meetings, Calls, Recruiters/Users,
Job Statuses, Candidate Statuses/Stages.

Never assume all of these exist for a given account — confirm via
`prompts/discovery.md` first.

## Chart type defaults by insight shape

- Stage-by-stage funnel volumes → Funnel
- Trend over time (single series) → Line
- Trend over time (multiple series/categories) → Area or combo — if combo
  mixes series types (e.g. category breakdown as bars + a total line), see
  CLAUDE.md "Combo chart series display" before setting `series_settings`
- Categorical comparison (e.g., by recruiter, by client) → Bar / stacked bar
- Single headline number → KPI
- List of specific records needing follow-up (e.g., stalled jobs) → Table
- Relationship between two continuous measures → Scatter

## Value formatting (CLAUDE.md "Value formatting")

Every displayed value must carry the unit its data actually represents —
never a bare number for something that isn't just a plain count. Judge by
what the field/measure actually is, not by name-pattern-matching alone:

- **Monetary** (deal value, budget/salary/package fields, cost/revenue,
  anything priced) → currency formatting
  (`number_style: "currency", "currency": "<ISO 4217 code>", "currency_style": "symbol"`
  in `column_settings`). The ISO code always comes from asking the user once
  per account (see CLAUDE.md "Value formatting") — never defaulted to `$`/USD.
- **Rate/ratio expressed as a share of a whole** (conversion rate, % placed,
  % of candidates by source) → `number_style: "percent"`.
- **Rate/ratio expressed as a multiple** (e.g. "Assigned : Placed") → a
  plain number with a `suffix` like `" : 1"`, not percent — it isn't a share
  of 100.
- **Duration** (time to fill, time in stage) → a plain number with a
  `suffix` for its unit (`" day(s)"`, `" sec"`, etc.) — pick the unit that
  matches what the query actually computes (don't relabel seconds as days).
- **Plain count** (records, candidates, jobs) → no special formatting;
  a bare number is correct here.

When unsure which bucket a field falls into, treat it as a plain number
rather than guessing at a unit — an unformatted number is a smaller error
than a wrongly-labeled one.

## Data labels (CLAUDE.md "Data labels")

- Bar / stacked bar / line / area / row / combo / funnel → `"graph.show_values": true`.
- Pie → `"pie.percent_visibility": "inside"` or `"both"` (not `"off"`).
- Scatter → point-level labels aren't standard for a scatter's density; a
  clear axis/legend is sufficient — don't force `graph.show_values` here.
- Table / pivot table / scalar / smartscalar / progress (KPI) → no setting
  needed; every value is already directly visible.
