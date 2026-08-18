# Analysis configuration

Defaults and knobs for the recommendation engine. Adjust here rather than in
CLAUDE.md if these need to change per-deployment.

## Defaults

- Default recommendation count if the user ever just says "some": 5
- Minimum record count to trust a distribution/trend as meaningful: judge in
  context, but treat anything under ~20 records as "too small to trust" for
  that specific slice, and say so rather than silently recommending it.
- Minimum history to call something a "trend": at least a few periods of the
  chosen granularity (e.g., 3+ months for a monthly trend) — a single data
  point is a fact, not a trend.

## Candidate entities (adapt to what actually exists per account)

Candidates, Companies/Clients, Contacts, Jobs, Job Assignments/Pipeline
Stages, Placements, Deals, Notes, Tasks, Meetings, Calls, Recruiters/Users,
Job Statuses, Candidate Statuses/Stages.

Never assume all of these exist for a given account — confirm via
`prompts/discovery.md` first.

## Ranking weights (relative priority, not a strict formula)

1. Business impact
2. Strength of observed pattern
3. Actionability
4. Data reliability
5. Relevance to recruitment operations
6. Uniqueness vs. existing Metabase content
7. Clarity of communication

## Chart type defaults by insight shape

- Stage-by-stage funnel volumes → Funnel
- Trend over time (single series) → Line
- Trend over time (multiple series/categories) → Area or combo
- Categorical comparison (e.g., by recruiter, by client) → Bar / stacked bar
- Single headline number → KPI
- List of specific records needing follow-up (e.g., stalled jobs) → Table
- Relationship between two continuous measures → Scatter
