## The prompt (copy everything below into Claude Code)

```
I want to upgrade an existing Claude skill called `metabase-question-workflow`
(SKILL.md attached/available in this project) so that chart-generation requests
for our recruiting CRM get built faster and more accurately. The skill's current
process is good — don't rewrite the 8-step workflow logic. What's missing is
grounded reference material the workflow can look up instead of rediscovering
per request. Do the following:

1. SCHEMA MAP
   Use the `mb` CLI / Metabase MCP connector to inspect our core tables:
   candidates, companies, contacts, call_logs, assigned_job_candidates, and any
   other tables that clearly relate to these (foreign keys pointing in/out).
   For each table, document: columns and types, primary/foreign keys, what one
   row represents (the grain), which columns are commonly filtered/grouped on,
   and any quirks (soft-delete flags, nullable FKs, duplicate-prone columns,
   date columns that don't mean what their name implies). Also note approximate
   row counts so the "GUI query vs. model vs. pre-aggregate" decision in step 4
   of the skill can be made from real numbers instead of a guess.
   Write this to references/schema-map.md.

2. EXISTING WORK AUDIT
   Search existing Metabase questions, models, and dashboards. Instead of
   re-searching per request (current step 3), produce a one-time index:
   what exists, what entity/metric it covers, and whether it's a model worth
   building new questions on top of. Write this to references/existing-work-index.md,
   and flag near-duplicates you find (multiple questions answering the same thing
   slightly differently) — this alone is worth telling me about even before
   the rest of this task is done.

3. METRIC GLOSSARY — needs my input, ask me directly
   Before writing this file, ask me to define the following terms precisely
   (don't guess): "active candidate," "placed" / "closed," "call outcome"
   categories and what each means, "assigned" (does this mean created,
   confirmed, or something else — and by whom), and how "this month" /
   "recent" should resolve when a request doesn't specify which date column.
   Ask about any other term you notice is ambiguous once you've seen the
   schema in step 1. Write the confirmed definitions, plus the exact
   column/filter that implements each one, to references/metric-glossary.md.

4. CANONICAL QUESTION PATTERNS
   From the existing-work audit and the schema, identify the 8-12 chart
   requests that are clearly recurring shapes for a recruiting CRM (e.g. call
   volume by rep/day, candidate funnel by stage, time-to-fill, candidate
   source breakdown, company/contact pipeline health, call outcome
   distribution). For each: the exact tables/join, the grain, the correct
   chart type, and a one-line description of when a new request matches it.
   Write this to references/canonical-patterns.md. This becomes the first
   thing checked on any new request — reuse before rebuild.

5. STARROCKS GOTCHAS
   Pull together the StarRocks-specific function/syntax gotchas relevant to
   how we actually query (date truncation, approximate distinct counts,
   window function support, anything you hit while doing steps 1-2) into
   references/starrocks-notes.md, so this is looked up once and reused
   instead of re-checked against docs on every native SQL question.

6. UPDATE THE SKILL
   Revise metabase-question-workflow's SKILL.md to:
   - Insert a step 0: check references/canonical-patterns.md for a match
     before doing full entity/table discovery.
   - Point steps 2-6 at the new reference files instead of "go inspect via
     mb/MCP" as the first move — inspection becomes the fallback for what
     the reference files don't cover, not the default.
   - Add a validation step after building: cross-check the result against a
     raw count/independent number before naming and saving it, and say what
     that check was when reporting back.
   - Add an explicit naming convention (propose one based on what's already
     in use per the existing-work audit; ask me to confirm it).
   - Add a short note on handling a batch of requirements at once (a client
     doc listing several asks): group by shared entity/model before building,
     so shared logic isn't rebuilt per chart.
   Keep the file lean — the reasoning stays in SKILL.md, the lookup tables
   live in references/.

7. REPORT BACK
   Summarize: what you found in the schema that surprised you, which existing
   questions look duplicated, and the metric definitions you need from me
   before the glossary is complete.

Do steps 1 and 2 first (pure inspection), then come to me with the metric
questions from step 3 before finishing the rest.
```

---
