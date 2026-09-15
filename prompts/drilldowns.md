# Drill-downs

Full method, confirmed `click_behavior` shapes, and known gotchas for wiring
drill-downs onto a dashboard's cards. The policy-level rules — which display
types need one, the confirm-before-building gate, where these cards live —
are in CLAUDE.md's "Drill-downs" section; this file is the how-to it points
to.

Every card added to a dashboard this project assembles should carry an
explicit `click_behavior` wherever a sensible drill target exists — a
summary bar/segment/KPI should let the viewer get to more detail in one
click (e.g. clicking a recruiter's bar on "Placements by Recruiter"
cross-filters the dashboard to that recruiter, or opens a detail table
already filtered to them). Load the `visualization` skill for the full
`click_behavior` catalog before wiring one — it's configured per-dashcard
when the card is added to the dashboard, not on the card definition itself.

**Always build drill-downs after the dashboard is finalized, never in the
same pass as the cards/layout — and confirm with the user before starting
them.** Per "Never write a native-SQL query to build one of these — reuse
the report's own MBQL construction verbatim" below, a drill-down's entire
correctness rests on copying its source report card's `dataset_query`
exactly as it stands — its joins, expressions, and filters. A report card
built earlier in the same session can still change shape before the user
is done (a filter added, a join adjusted, a column renamed), and a
drill-down built against an intermediate version of it silently drifts out
of sync the moment the report changes again. So: finish assembling the
dashboard (cards placed, layout, filters/parameters, documentation tab —
see step 9-10 of the "Requirements Intake flow" in CLAUDE.md), consider it
finalized, **then** ask the user for a plain yes/no confirmation before
building any drill-downs, and only then work through the rest of this
section against each report card's now-final construction.

**This is a strict requirement across every chart display this project
uses, not just bar/row charts.** Every dashcard of the following `display`
types must carry an explicit `click_behavior` (crossfilter or custom
destination, per the decision rule below) wherever a sensible drill target
exists: **bar, row, pie, line, area, combo, scatter, treemap, map, box
plot (box), funnel, waterfall, sankey, gauge, progress, trend, and number**
— including a plain ungrouped-grand-total scalar/KPI with no breakout
dimension of its own, as long as the dashboard has at least one filter
actually bound to that card (see "Single-metric, non-tabular chart
click_behavior" below for why an ungrouped number still has a genuine
drill target in that case) — plus **table and pivot table, but only when the card's query includes an
aggregation/summarize step** — a plain unaggregated record list has no
"more detail" to drill into and is itself the most granular view (see the
"skip it" carve-out below). A chart type appearing on a dashboard this
project assembles or adds to is never exempt from this list by omission —
if a card's `display` is one of these and it lacks a `click_behavior`
after the "skip it" carve-out is checked and doesn't apply, that is a gap
to fix, the same as a missing chart or a missing documentation tab.
Single-metric, non-tabular displays (treemap, pie, gauge, progress, trend,
number, map, box plot, funnel, waterfall, sankey) get **one dashcard-level
`click_behavior`** covering the whole chart (there's no per-column
concept); tabular displays (table, pivot table) that carry more than one
metric column use the **per-column `click_behavior` under
`column_settings`** instead, per "Drilling into one aggregated metric out
of several on the same card" below — don't leave a multi-metric table/pivot
with only a whole-card crossfilter when its individual metric columns each
have their own genuinely-more-detailed drill target available.

- Prefer **cross-filtering other cards on the same dashboard** ("Update a
  dashboard filter") when the dashboard already has, or is getting, a filter
  covering the clicked dimension. Use "Go to a custom destination" (another
  question/dashboard, pre-filtered) only when a genuinely more detailed view
  exists for that value.
- Skip it where it adds nothing: a KPI/scalar with genuinely no natural
  drill target (no dashboard filter is bound to it *and* it has no
  dimension of its own — see "Single-metric, non-tabular chart
  click_behavior" below before assuming this is the case), a card that's
  already the most granular view on the dashboard, or a text card on the
  documentation tab (see CLAUDE.md "Dashboard documentation") — those never
  carry a `click_behavior`.
- Only point a drill-down at content this project actually created (this
  session or a prior one) or content the user has explicitly named as a
  destination — never guess at an existing dashboard/question to link to.

**Drilling into one aggregated metric out of several on the same card.** A
card like a stage/funnel breakdown table often carries **several named
aggregations as separate columns** (e.g. "Unqualified", "Uncontacted",
"Prescreen", "Hired" — each its own `distinct-where` aggregation with its
own filter condition). A single generic detail table filtered only by the
card's dimension (source, job, etc.) is **not** an adequate drill-down for
this shape — clicking the "Hired" cell and clicking the "Unqualified" cell
for the same row would land on the identical unfiltered-by-stage list,
which does not actually show "the underlying data for this metric."

**Reusing an existing drill-down card across more than one chart.** More
than one chart on a dashboard can carry what looks like the same named
metric — e.g. a funnel table's "Candidates Added" column and a separate
treemap/pie/KPI also labeled "Candidates Added." **Reuse a single
drill-down card across charts only when the charts' underlying
`dataset_query` construction is exactly the same for the relevant piece —
the same `source-table`, the same `joins` (including whether a join to a
"current stage" Model exists at all), the same `expressions`, and the same
base `filters` — never just because the aggregation function and display
name match.** Confirm this by pulling both cards' full `dataset_query`
(`mb card get <id> --full --json` on each) and diffing the pieces above
before wiring a shared target — don't assume identical metric names imply
identical underlying queries. Two cards can compute a matching aggregate
value for a given slice today and still not be "the same logic": a chart
built directly off the base table (no join) and a chart that reaches the
same number by joining a Model add a real construction difference — even
if a left join happens not to change *that* aggregate's arithmetic, it
changes what "the underlying data for this metric" actually consists of
(the joined chart's drill-down would carry the Model's own dimensions —
job/company/hiring-stage columns — that the un-joined chart's query never
touches, and can show a different row count once the Model's data or
ranking shifts, since the un-joined chart's own number never depended on
that join to begin with). Reusing an existing drill-down here means
borrowing a construction the clicking chart doesn't actually have. When
construction diverges, build a **separate** drill-down for the diverging
chart, following the same "copy verbatim, never re-derive" method below —
just source it from **that chart's own** `dataset_query`, treating it as
its own "report," rather than a sibling chart's.

**Never write a native-SQL query to build one of these — reuse the
report's own MBQL construction verbatim, never re-derive it.** This is not
the usual "GUI first, native SQL when MBQL genuinely can't express it"
judgment call from CLAUDE.md's "Chart creation" — for a drill-down
specifically, hand-writing *any* version of the report's logic (SQL or
MBQL, however carefully transcribed) is a correctness risk with no upside:
every value these cards need (the base table, the join to a "current
stage" Model, a bucketing expression, each metric's filter condition)
**already exists, already correct, in the report card itself.** Copying it
byte-for-byte guarantees the drill-down's logic can never drift from the
report's; typing any of it out by hand — even to translate MBQL into
equivalent SQL — reintroduces exactly the drift risk this rule exists to
eliminate. Concretely:

1. `mb card get <report-card-id> --full --json` and pull the report's
   `joins`, `expressions`, and base `filters` straight out of the
   `dataset_query` — verbatim, not retyped. Read each named aggregation's
   condition (the 4th element of a `distinct-where`/`count-where` clause)
   the same way — e.g. "Unqualified" might be `hiring_stage IS NULL OR
   hiring_stage = 'Applied'`, "Hired" might be `hiring_stage IN ('Hired',
   'Placed')`. Copy these verbatim too; don't guess a single-value equality
   when the real condition is a compound OR/IN.
2. Build each drill-down card as an **MBQL query**: the same `source-table`,
   the same `joins` array (a join to a Model is a `source-card` join —
   reuse it as-is so the drill-down goes through the *exact same* ranking
   computation as the report, not a re-implementation of it), the same
   `expressions`, the base filter plus that one metric's condition, **no
   aggregation** (a plain row list) — except when the report's own
   aggregation for this metric is a distinct count (see the de-duplication
   step immediately below, which replaces this plain-row-list shape for
   that case). Restrict the output columns via the **join's own `fields`**
   as an explicit list of what's actually needed — never `"all"` — per the
   `fields`-reliability gotcha below; this also keeps unrelated (and
   potentially sensitive) columns from a wide Model out of the drill-down
   entirely, not just hidden from view.
3. **When the metric being drilled into is a distinct-count aggregation on
   the report (`distinct` or `distinct-where`), don't leave the drill-down
   as a plain, unaggregated row list — add a Group By layer breaking out on
   every one of the drill-down's own displayed columns *plus the exact
   field the report's `distinct`/`distinct-where` aggregates on* (the
   entity id — e.g. the candidate id), with no aggregate function.**
   Concretely: take the row-list query from step 2 and move its `fields`
   list to `breakout` instead, **adding the id field to that list even
   when it isn't one of the columns the drill-down actually displays** —
   hide it from the visible table via `visualization_settings.table.columns`
   (an `{"name": "<id column>", "enabled": false}` entry) rather than
   leaving it out of the query entirely. No `aggregation` clause is added.
   This is the GUI/MBQL equivalent of `SELECT DISTINCT` over the drill-down's
   displayed columns *and* its id — not `SELECT DISTINCT` over the displayed
   columns alone. **The id must be part of the group-by set, not just the
   human-readable columns**: grouping only by what's on screen (name,
   source, stage, etc.) can silently collapse two genuinely different
   records into one row whenever their *displayed* values happen to match —
   confirmed on account 44663, where two different candidates named
   "Francisco Rodriguez" referred by the same raw source collapsed into a
   single row under a name+source-only group-by, undercounting that
   source's drill-down by one real candidate. Grouping by id-plus-columns
   instead of columns-alone still collapses true duplicate rows (identical
   in every column, id included — the join-fanout/tiebreak noise this step
   targets) while never merging two distinct entities that only *look*
   alike on the columns actually shown. The duplicate-row noise this step
   targets in the first place comes from a join to a table that carries
   duplicate `id` values (Assignments, Deals, Pitched Candidates,
   Notes/Tasks/Meetings — see CLAUDE.md "Recruit CRM / Metabase data
   model") or a tie in a ranking Model's `ORDER BY` (see the tiebreaker
   fragility noted below) — either can hand the drill-down literal
   duplicate rows, identical in every column including the id, that
   inflate its row count with no new information; genuinely different rows
   for the same entity (e.g. the same candidate's two different job
   assignments, which differ in `job_name`/`company_name`/etc.) stay
   untouched — that difference is real detail, not noise, per the
   "more-granular, not a bug" note in the verify step below. Confirmed on
   account 44663's Sourcing Funnel drill-downs: this step alone does not
   guarantee an exact row-count match against the report's
   distinct-candidate total (a candidate legitimately reaching the same
   stage via more than one job still yields one row per job) — it only
   removes duplicate-row noise that has no such legitimate explanation.
4. **Verify before wiring, and verify a filtered slice, not just the
   grand total**: take one breakout value that actually appears in the
   report (e.g. one source), copy the drill-down's query, append a literal
   filter for that exact value (`["=", {}, ["expression", {}, "Source -
   Category"], "Indeed"]`), run it with a `distinct` aggregation on the
   candidate id field, and confirm it **matches that exact cell** in the
   report — not an approximation. A metric whose underlying rows are
   naturally one-per-pairing rather than one-per-candidate (e.g. a stage
   reached via more than one job assignment) will legitimately return
   **more rows** than `COUNT(DISTINCT candidate)` for that metric when the
   card is actually opened, even after step 3's de-duplication — that's the
   correct, more-granular detail, not a bug. What step 3 eliminates is any
   *further* excess beyond that legitimate per-pairing count — spot-check
   this by comparing the drill-down's post-de-dup row count against its own
   pre-de-dup row count for the same filtered slice: any drop confirms real
   duplicate-row noise was removed; a remaining gap versus the report's
   distinct count is expected when candidates genuinely reach the metric's
   stage through more than one pairing.
5. **Wire it as a per-column `click_behavior`: "Go to a custom
   destination" → that metric's own drill-down card, with "Pass values to
   filter this question"** — this is a UI path that genuinely does apply
   an ad-hoc dimension filter to a plain MBQL destination card. See "The
   confirmed `click_behavior` shape for custom-destination filtering"
   below for the exact JSON — **it does not match the shape a plausible
   first reading of the `visualization` skill's click-behavior reference
   suggests**, and two earlier attempts in this project guessed at a
   shape that looked reasonable, round-tripped through the API with no
   validation error, and simply didn't filter anything when clicked. Don't
   repeat that: use the confirmed shape below, or better, find and copy an
   existing working example already in this Metabase instance (search for
   dashboards with a name like the report's own domain, `mb dashboard
   cards <id> --full --json`, and look for a dashcard whose
   `visualization_settings.click_behavior.parameterMapping` is non-empty)
   — the "don't hand-author, copy a UI-built one" rule the `visualization`
   skill already states applies with extra force here. Into that mapping,
   pass **every dimension the clicked chart groups by** (as a `column`
   source) **plus every dashboard filter actually bound to that chart** (as
   a `parameter` source) — not just the one that comes to mind first. A
   chart grouped by source only needs that source value passed through; a
   chart grouped by job *and* source needs both — and a drill-down card
   shared between a source-only chart and a source+job chart simply has no
   mapping entry targeting its job dimension when clicked from the
   source-only chart (unmapped = unrestricted by job there, which is
   correct). Match each dashboard-filter pass-through to the **exact
   field the source chart itself binds that filter to** (check the
   chart's own `parameter_mappings` via `mb dashboard get`) — a
   dashboard's "Date" filter is not necessarily bound to the same field on
   every card in it (one card's Date filter might target
   `candidates.created_on`, a sibling card's might target a
   job-creation field instead); passing the wrong one produces a
   drill-down whose total is close but not exact.
6. These are drill-down/detail cards backing this dashboard's
   `click_behavior` targets — they belong in the account's
   `Drill-downs` → `<Dashboard Name> Drill-downs` sub-collection per
   CLAUDE.md "Where created charts live", one dedicated sub-collection
   whether there are one or many.

**Entity profile links in drill-down columns.** Whenever a drill-down
displays a candidate name, company name, job name, or contact name — which
it almost always will — also surface that entity's profile link, not just
its plain-text name. Recruit CRM stores a profile URL as its own field on
each entity's own table: by convention `candidate_profile` (Candidates),
`company_profile` (Companies), `job_profile` (Jobs), `contact_profile`
(Contacts) — **confirm the exact field name and id for this account with
`mb table fields <table-id>` before using it, the same as any other field;
never assume the name carries over unverified.** Verified working end to
end on account 44663's "Candidates Added — Candidate Detail" card (75524)
— use it as the reference shape:

1. **If the entity's own table is already the drill-down's source table or
   already joined directly** (e.g. the candidate's own table, since a
   candidate drill-down's `source-table` already *is* Candidates), the
   profile field is already a sibling column — no new join needed, just
   add it to the query.
2. **If the entity's name is surfaced via a joined Model rather than a
   direct join to that entity's own table** (e.g. `job_name`/`company_name`
   here come from the `Latest Candidate Stage Model` join, not a direct
   Jobs/Companies join) **and the drill-down doesn't otherwise have the
   respective table joined, add a left join to that entity's own table**
   — joined on the FK the Model itself already exposes for this purpose
   (e.g. `Latest Candidate Stage Model` carries `join_for_jobs_table`,
   `join_for_companies_table`, and `join_for_contacts_table` — check
   `mb card get <model-id> --json --fields result_metadata` for the
   model actually in use rather than assuming these names). **Join on that
   FK, never on the text name column** — names aren't reliably unique, and
   a join on the id the Model already carries is both correct and free
   (the value already exists in the query, no extra lookup needed). A join
   added purely for a profile field needs no other purpose — restrict its
   `fields` to just the profile column, per the `fields`-reliability
   gotcha below.
3. **Add the profile field to the breakout** (per the group-by-all-columns
   dedup rule above), alongside the entity's own name field it accompanies.
4. **Display the profile field in place of the plain-text name, not
   alongside it**: hide the plain name column
   (`table.columns` entry `{"name": "<name column>", "enabled": false}`)
   and show the profile column instead (`enabled: true`). Format the
   profile column's `column_settings` with `"view_as": "link"` (set this
   explicitly — don't rely on the field's own `semantic_type` to
   auto-render it as a link; `company_profile` on account 44663 carries
   `semantic_type: "type/Company"`, not `type/URL`, so it needs the
   explicit override even though `candidate_profile`, which happens to
   carry `type/URL`, might render as a link without it), `"link_text":
   "{{<name column>}}"` (the mustache template pulls in the plain name as
   the link's visible text, so the cell reads as the entity's name while
   still linking to its profile), and `"column_title": "<Entity> Name"`
   (e.g. "Candidate Name", "Company Name", "Job Name") to rename the
   header away from the raw field name.

**Every dashboard filter passed into a drill-down must also be a visible
column on it — never a silent filter with nothing to show for it.** When
wiring a drill-down's `click_behavior` (per "Wire it as a per-column
`click_behavior`" above), every dashboard parameter passed through as a
`"parameter"` source targets some field on the drill-down's own query —
that exact field must also appear as a displayed column (added to the
breakout and left visible in `table.columns`), not just live in the query
as an invisible filter target. Confirmed missing on account 44663 before
this fix: every drill-down reachable from the "Sourcing Funnel" table and
"Candidates Added by Source" treemap gets the dashboard's Date filter
passed through against `created_on` (the base Candidates field those two
charts bind Date to), but none of the drill-downs displayed a `created_on`
column at all — a viewer opening one had no way to see what date value
each row actually carried, only that *some* filter had silently narrowed
the list. A drill-down whose filtered population a viewer can't actually
see the filtered-on value for isn't trustworthy or self-explanatory.
**Different source charts on the same dashboard can bind the same
dashboard filter to different fields** (e.g. the pivot binds Date to
`job_created_on` instead) — per "Match each dashboard-filter pass-through
to the exact field the source chart itself binds that filter to" above, a
drill-down shared by more than one source chart may need **more than one**
such column if the charts that link to it bind the same dashboard filter
to different fields on it.

**Drill-downs should show enough to be independently meaningful, not just
the bare minimum needed to answer the metric.** A drill-down exists so a
business user can act on what they see — recognize who's in the list and
do something about it — not just confirm a count. Beyond the mechanical
requirements above (the metric's own dimensions, entity profile links,
filter-bound fields), add a modest number of genuinely useful context
fields already available on the same base or joined tables — for a
candidate list, for example, an `email` column so the list is directly
actionable without another lookup. Don't pad a drill-down with every
available column on the off chance it's useful — per CLAUDE.md "Data
quality gate" and the spirit of this whole project, add what a business
user reviewing this specific list would actually want, and stop there.

**The confirmed `click_behavior` shape for custom-destination filtering.**
Verified by finding a genuinely UI-built example already in this Metabase
instance (the "Revenue Summary" dashboard in a client's shared collection
has dozens of these) and reading its stored JSON directly — this is the
"escape hatch" the `visualization` skill recommends, used because two
prior hand-authored guesses at this shape were both wrong in ways that
looked plausible and produced no error. The **target** side of each
mapping entry is not the simple `{id, type}` a first read of the generic
click-behavior reference suggests — it carries the *entire* dashboard-style
dimension reference twice over, and the map key is that reference too, not
an arbitrary UUID:

```jsonc
{
  "type": "link",
  "linkType": "question",
  "targetId": 42506,                 // the destination's numeric card id
  "parameterMapping": {
    // the map KEY is the JSON string form of the target array below (compact, no spaces)
    "[\"dimension\",[\"field\",\"job_name\",{\"base-type\":\"type/Text\",\"join-alias\":\"Latest Candidate Stage Model\"}],{\"stage-number\":0}]": {
      "source": { "type": "column", "id": "job_name", "name": "job_name" },
      "target": {
        "type": "dimension",
        "id": "[\"dimension\",[\"field\",\"job_name\",{\"base-type\":\"type/Text\",\"join-alias\":\"Latest Candidate Stage Model\"}],{\"stage-number\":0}]",
        "dimension": ["dimension", ["field", "job_name", {"base-type": "type/Text", "join-alias": "Latest Candidate Stage Model"}], {"stage-number": 0}]
      },
      "id": "[\"dimension\",[\"field\",\"job_name\",{\"base-type\":\"type/Text\",\"join-alias\":\"Latest Candidate Stage Model\"}],{\"stage-number\":0}]"
    }
  }
}
```

Rules confirmed from that real example (63 dashcards' worth, spanning
every combination):

- The `<field-ref>` inside `["dimension", <field-ref>, {"stage-number": 0}]`
  is exactly the same grammar as a dashboard's own `parameter_mappings`
  target — `["field", <numeric-id-or-string-name>, {options}]` for a table
  column (string name once it's past a join/expression, e.g. from a
  `source-card` join — add `"join-alias"` there same as any other joined
  field reference) or `["expression", "<name>", {options}]` for a custom
  column — **not** the bare `{id, type: "dimension"}` a generic reading of
  the click-behavior key catalog implies.
- Both the outer `parameterMapping` **map key** and the inner `target.id`
  and the mapping entry's own top-level `id` are the **identical string**:
  the compact (no whitespace) JSON serialization of that
  `["dimension", <field-ref>, {"stage-number": 0}]` array — a derived,
  deterministic id, never a minted UUID.
- `source.type` is `"column"` (a dynamic value from the clicked row —
  `id`/`name` are the output column name) to pass through something the
  chart groups by, or `"parameter"` (the *current* value of an existing
  dashboard parameter — `id` is that parameter's id, `name` is free text)
  to pass through a dashboard filter. This confirms `click_behavior` on a
  plain MBQL destination genuinely does support ad-hoc dimension
  filtering via this exact shape — it is not native-SQL-only.
- `mb card get <target-id> --full --json` on the destination in that real
  example confirms it: a plain `mbql.stage/mbql` question, no template
  tags, no declared `parameters` array of its own. The destination needs
  none of that — the whole filter definition lives in the *clicking*
  card's `click_behavior`, not in anything the destination card declares.

**A separate, pre-existing fragility this surfaced, unrelated to how the
drill-down is built:** the "current/furthest stage" ranking (`ROW_NUMBER()
OVER (PARTITION BY id ORDER BY updated_on DESC, <stage-ordinal> DESC)`, per
CLAUDE.md "Determining a candidate's current/furthest pipeline stage") has
no tiebreaker after the ordinal — two rows tied on both `updated_on` and
ordinal can rank arbitrarily, and *which* row wins can depend on the
surrounding query's shape (join order, what else is being computed
alongside it), not just on the row data. Observed directly: a drill-down
built by reusing the report's own join (not a re-implementation) still
came back 1–3 records off the report's grand total on 4 of 10 metrics,
while every *filtered-slice* spot check (one metric × one source, or one
metric × one source × one job) matched exactly — the variance only shows
up in the full, unfiltered aggregate, and re-running the identical
aggregate query repeatedly returned a stable (not randomly flapping)
answer, meaning the two query *shapes* (the report's multi-metric
aggregation vs. a single-metric count) each settle on their own consistent
but *different* tie-break, not that either is flaky in isolation. This is
a latent defect in the Model's own ranking definition (present in any
Model or query using this ORDER BY pattern, not specific to drill-downs,
and arguably already affecting the report's own displayed numbers) — a
deterministic final tiebreaker (e.g. `, id DESC`) would fix it at the
source for the report and every drill-down at once. Worth raising with the
user as a distinct, optional fix (it can shift already-reviewed totals by
a record or two) rather than folding it silently into a drill-down task.

**Single-metric, non-tabular chart click_behavior (bar, row, pie, line,
area, combo, scatter, treemap, map, box plot, funnel, waterfall, sankey,
gauge, progress, trend, number).** Everything in "The confirmed
`click_behavior` shape for custom-destination filtering" above was framed
around a table's **per-column** `click_behavior` (nested under
`column_settings`). A chart with only one metric has no separate "column"
to hang that on — the *entire dashcard* gets **one** `click_behavior`,
set directly on `visualization_settings.click_behavior` (the same location
a crossfilter would occupy), not nested under `column_settings`. Verified
against a genuinely UI-built example already in this Metabase instance —
the "Revenue Summary" dashboard's "Overview" tab has dozens of these,
across scalar, bar, and line cards alike:

- **A chart with its own breakout dimension** (e.g. a bar chart broken out
  by employment type) passes that dimension through as a `"column"` source
  — same as a table's metric column — **plus every dashboard filter
  actually bound to that card** as `"parameter"` sources, keyed exactly as
  in the per-column recipe above (one `parameterMapping` entry per
  dimension/filter, each keyed by the compact JSON form of its own
  `["dimension", <field-ref>, {"stage-number":0}]`).
- **A plain scalar/KPI with *no* breakout dimension of its own is not
  exempt from this** — confirmed directly: every scalar on that Overview
  tab ("Total Sales," "Total Placements," "Current Weekly GP," etc.) carries
  a dashcard-level `click_behavior` whose `parameterMapping` consists
  **entirely of `"parameter"` sources** (no `"column"` entries at all, since
  clicking an ungrouped number has no per-click dimension value to pass
  through) — one entry per dashboard filter bound to that card (Date, Team,
  Company, Team Member, Period, …), each passing the filter's *currently
  applied* value into the destination as an ad-hoc dimension filter. The
  destination is the same underlying detail question a sibling breakout
  chart on the same tab links to (e.g. multiple different cards' "Total
  Sales"-family click_behaviors on that Overview tab all resolve to the
  same target question) — clicking the number takes the viewer to exactly
  the transactions currently contributing to it, at whatever filter state
  the dashboard is in. **This means "no natural drill target" is genuinely
  the exception, not the default, for a scalar/KPI that sits on a filtered
  dashboard** — check whether the dashboard has any filter bound to that
  card (`mb dashboard get <id> --fields parameters,dashcards.parameter_mappings`)
  before concluding a scalar has nothing to drill into; skip it only when
  neither a bound filter nor a dimension of its own exists to seed a
  meaningful ad-hoc filter on the destination.
- **Replacing an existing crossfilter with a custom-destination link is the
  normal way this gets wired**, not an edge case — a single-metric chart
  can only hold one `click_behavior` at a time, so per the "prefer
  crossfilter... use custom destination only when a genuinely more detailed
  view exists" rule above, adding a drill-down to a chart that already has
  a bare crossfilter means *replacing* that crossfilter's object at
  `visualization_settings.click_behavior` with the "link" object, not
  adding a second behavior alongside it. Done this way on account 44663's
  "Candidates Added by Source" treemap: it previously only crossfiltered
  the dashboard's Source parameter on click; since a detail card already
  existed, its `click_behavior` was replaced outright with a "link" to that
  detail card, reusing the exact `parameterMapping` shape already verified
  elsewhere on the same dashboard for the equivalent dimension/filter pair.

**Drill-downs for a pivot table.** A `pivot` display card with several
aggregation columns looks like the tabular case in "Drilling into one
aggregated metric out of several on the same card" above (several named
metrics that each need their own drill target), but it isn't wired the
same way — **a `pivot` card does not reliably honor a per-column
`click_behavior` under `column_settings` the way a plain `table` display
does.** In practice every click on a `pivot` card's cells — whichever
column — falls back to the single dashcard-level `click_behavior`, so
attempting the same "one link per metric column" recipe used for a
multi-metric `table` (confirmed working on account 44663's "Sourcing
Funnel" table, `display: "table"`) silently does nothing on a `pivot`
card: clicking any metric cell just re-fires whatever the dashcard-level
behavior is (typically the crossfilter), never the per-column link —
confirmed broken this way on account 44663's "Sourcing Funnel: Job" pivot
before this rule existed. **Do not keep trying to attach one
`click_behavior` per metric column to the pivot card itself — it can't
carry more than the one dashcard-level behavior that actually fires.**

Instead, give a pivot's drill-downs their own dedicated **drill-down
dashboard**, and let the pivot's single dashcard-level `click_behavior`
navigate to it:

1. Build one drill-down card per aggregation column on the pivot, same as
   any other drill-down (verbatim-copy the pivot's own `joins`,
   `expressions`, and base `filters` per the numbered steps above — the
   pivot is this drill-down's own "report," per "Reusing an existing
   drill-down card across more than one chart" above — plus that one
   metric's condition, the group-by-all-columns-plus-id dedup step,
   entity profile links, and every dashboard-filter-bound column, exactly
   as for any other drill-down).
2. Create a **new dashboard** dedicated to hosting these cards — named for
   the pivot (e.g. "`<Pivot card name>` Drill-down") — and add one dashcard
   per metric card onto it (a simple grid layout; no documentation tab
   needed, this dashboard is drill-down plumbing, not a client-facing
   report in its own right).
3. Give this new dashboard its own **filter parameters, one per dimension
   the pivot groups by** (e.g. a Job filter, a Source filter, a Company
   filter if the pivot breaks out by all three) — mapped onto the matching
   field on every one of its cards, the same ordinary dashboard-parameter
   mechanics used elsewhere in this project (load the `dashboard` skill
   for the mapping mechanics if it isn't already fresh in context).
4. Wire the **pivot's own dashcard-level `click_behavior`** as a "Go to a
   custom destination" **dashboard** link (`linkType: "dashboard"`, not
   `"question"`) targeting this new dashboard, with `parameterMapping`
   passing each of the pivot's own breakout dimensions (as `"column"`
   sources, same as the pivot's clicked-row values) into that dashboard's
   matching filter parameters, plus any dashboard filter already bound to
   the pivot (as `"parameter"` sources) — same "pass every dimension the
   chart groups by, plus every bound filter" principle as the per-column
   case, just landing on a dashboard's filters instead of a single card's
   ad-hoc field filter.

   **The confirmed `linkType: "dashboard"` shape** — verified on account
   44663's "Sourcing Funnel: Job" pivot linking to its own "Source Funnel:
   Jobs - Details" drill-down dashboard, built through the UI. It's
   materially simpler than the question-link shape in "The confirmed
   `click_behavior` shape for custom-destination filtering" above: the map
   key and `target` are just the **destination dashboard's own parameter
   id** (a short opaque string like `"ad85a003"`, from that dashboard's
   `parameters` array) — no compact dimension-array JSON string, no
   `["dimension", <field-ref>, {...}]` grammar, because the destination
   dashboard's own per-dashcard `parameter_mappings` (the ordinary
   dashboard-filter mechanism, already documented elsewhere in this
   project) does the actual field targeting on each card individually:

   ```jsonc
   {
     "type": "link",
     "linkType": "dashboard",
     "targetId": 20726,                 // destination dashboard's numeric id
     "parameterMapping": {
       "ad85a003": {                    // destination dashboard parameter id (map key == target.id)
         "source": { "type": "column", "id": "job_name", "name": "Latest Candidate Stage Model → job_name" },
         "target": { "type": "parameter", "id": "ad85a003" },
         "id": "ad85a003"
       },
       "38c9ac2f": {                    // the dashboard's own bound Date filter, passed straight through
         "source": { "type": "parameter", "id": "5070ca14", "name": "Date" },
         "target": { "type": "parameter", "id": "38c9ac2f" },
         "id": "38c9ac2f"
       }
       // one entry per breakout dimension (source: column) and per bound filter (source: parameter)
     }
   }
   ```

   On the **destination dashboard's side**, each of its own filter
   parameters (Date, Source, Company Name, Job Name in the confirmed
   example) gets mapped per-dashcard via ordinary `parameter_mappings`, one
   entry per card — this is unchanged from how any dashboard filter is
   wired to any card, nothing new. One quirk worth copying verbatim rather
   than re-deriving: in the confirmed example, the Date filter's mapping
   target on each card addresses the joined date field by its **full
   desired-column-alias name and `stage-number: 1`**
   (`["dimension", ["field", "Latest Candidate Stage Model__job_created_on",
   {"base-type": "type/DateTime", "inherited-temporal-unit": "default"}],
   {"stage-number": 1}]`) rather than the plain `stage-number: 0` +
   `join-alias` form used for the same field elsewhere in this project —
   copy this exact addressing per field from a working mapping instead of
   assuming the stage-0 form always applies; the same "don't hand-author,
   copy a UI-built one" principle governs `parameter_mappings` targets, not
   just `click_behavior` ones.
5. Place the new dashboard directly in the account's **`Drill-downs`**
   sub-collection itself — not nested inside `<Dashboard Name>
   Drill-downs` with the cards — per CLAUDE.md "Where created charts
   live"; its backing metric cards still go in `Drill-downs` → `<Dashboard
   Name> Drill-downs` as usual. This dashboard is drill-down infrastructure
   for the pivot, not a primary destination, so it's never pinned the way
   a client-facing dashboard is.

**Known Metabase gotchas hit while building this (all confirmed on
v1.63.16 — re-verify if the instance is on a materially different
version):**

- **When a `click_behavior` or other `visualization_settings` shape is
  uncertain, don't iterate on plausible-looking hand-authored JSON —
  find a genuinely UI-built example already in this Metabase instance and
  copy its exact structure.** This project guessed wrong twice in a row on
  the custom-destination `click_behavior` shape (see "The confirmed
  `click_behavior` shape for custom-destination filtering" above) — both
  guesses were internally consistent, round-tripped through the API with
  no validation error, and simply didn't work when actually clicked, which
  reads identically to "the feature doesn't support this" right up until a
  real example proves otherwise. `mb search <term> --models dashboard`
  across the whole instance (not just the current account) plus `mb
  dashboard cards <id> --full --json` to pull every dashcard's full
  `visualization_settings` is usually enough to find one — a dashboard
  covering a similar domain, or literally any dashboard with heavy
  drill-down usage, is a better source of truth than reasoning about the
  key catalog from first principles. The `visualization` skill already
  says "don't hand-author a complex click_behavior — copy a UI-built one";
  treat that as load-bearing, not optional, for anything beyond the
  simplest crossfilter.
- **`mb card query --parameters` does not exercise the same code path as
  real dashboard click-through navigation — a negative result from it is
  not proof a `click_behavior` mechanism is broken.** Confirmed on account
  44663: a plain-MBQL custom-destination drill-down tested "broken" via
  `mb card query --parameters`, which was read as "ad-hoc/click-through
  parameters can't be resolved on an MBQL question in this version" and
  triggered a full rebuild — first to native SQL, then to a separate
  on-dashboard Detail-tab-with-`parameter_mappings` architecture — before a
  real UI-built example proved the original plain-MBQL `click_behavior`
  approach worked fine all along. If a click-through drill-down appears not
  to work, don't let an `mb card query --parameters` test decide it and
  don't rebuild to a different architecture on that basis alone — first
  find a confirmed UI-built example (per the "guessed wrong twice" bullet
  above) and check the wiring against it; there is currently no `mb`
  command that behaviorally exercises real click-through, so a negative
  CLI-level test is not equivalent to "this doesn't work."
- **`click_behavior` type `"link"`'s `targetId` must be the plain
  **numeric** card id** — not the entity id string that one skill example
  shows (`"Click behavior target id must be an integer"` is the server's
  own error when given an entity id).
- **When patching a dashboard's `dashcards` via `dashboard update`, always
  include the dashboard's current `tabs` array in the same request body —
  even when tabs aren't changing.** Omitting `tabs` while sending
  `dashcards` does **not** leave existing tabs alone; it clears them,
  which then breaks the foreign key from every dashcard's
  `dashboard_tab_id` to the (now-deleted) tab — surfacing as an opaque
  500, or as an explicit `fk_report_dashboardcard_ref_dashboard_tab_id`
  violation on a simpler retry. Always re-fetch and re-send `tabs`
  alongside `dashcards` on any update once a dashboard has tabs.
- **`dashboard update-dashcard` (the "safe single-dashcard patch" command)
  was unreliable for `visualization_settings` payloads that the full
  `dashboard update` (whole-`dashcards`-array replace) accepted without
  issue** — including a payload proven to work moments earlier via the
  full-array path. When a `update-dashcard` call on `visualization_settings`
  / `click_behavior` fails opaquely, fall back to a full `dashboard update`
  (re-fetching the current `dashcards` and `tabs` first) rather than
  fighting the single-dashcard patch.
- **An MBQL stage-level `fields` clause does not reliably restrict output
  columns when the stage also has a join whose own `fields` is `"all"`** —
  observed to work once, then return every one of the join's ~40 columns
  on an otherwise-identical re-run of the same query file. This is a real
  data-exposure risk, not just a cosmetic one: hiding unwanted columns
  only via `visualization_settings.table.columns` still leaves them
  reachable through the card's own CSV/Excel export regardless of what's
  visibly toggled off. **Fix at the join, not the display**: set the
  join's own `fields` to the explicit list of columns actually needed
  (never `"all"`) instead of relying on a downstream stage-level `fields`
  clause to narrow an over-broad join projection. Filters in the same
  stage as the join can still reference any joined column (confirmed via
  an unchanged aggregate count) even when that column is excluded from
  the join's own `fields` list — narrowing a join's `fields` does not
  break filtering on the columns you excluded from it.

## Completion audit — run once after wiring a batch of drill-downs

**Why this exists:** on account 44663's Sourcing Report dashboard, three
separate follow-up sessions each caught a different completeness gap in
the same batch of drill-downs *after* they'd already been wired and
reported as done — a breakout dimension (`company_name`) missing from a
pivot's per-metric `click_behavior` mappings, a filter-bound field
(`created_on`) passed through but never displayed, and no independently
actionable context field (`email`) on any of them. Every one of these
violated a rule already documented in this file at the time — the gap
wasn't a missing rule, it was that nothing re-checked the finished wiring
against the full rule set before calling it done. Don't repeat that:
before reporting a batch of drill-downs finished, audit every one of them
against the checklist below in one pass, rather than leaving gaps to
surface one at a time across future sessions.

**When:** immediately after wiring `click_behavior` for a batch of
drill-downs (the per-column recipe, the single-metric recipe, or the
pivot's dedicated drill-down dashboard) — before telling the user the
drill-downs are done, not as a separate follow-up task.

**How:** pull what you need in as few calls as possible rather than
relying on memory of what was just wired — `mb dashboard get <id> --fields
parameters,dashcards.parameter_mappings` once for the clicking dashboard
(every chart's bound filters and breakout dimensions in one call), then
`mb card get <drilldown-id> --full --json` for each drill-down card. For
every drill-down card (and every per-column mapping entry on a
multi-metric card), check:

1. **Every dimension the clicking chart groups by** is present in
   `parameterMapping` as a `"column"` source — re-checked against that
   chart's actual breakout list from `mb card get`, not memory of what was
   intended. A chart grouped by three dimensions needs all three, not just
   the one or two that came to mind first (see "Reusing an existing
   drill-down card across more than one chart" and the pivot-table
   section above for why this specifically slips).
2. **Every dashboard filter bound to the clicking chart** is present as a
   `"parameter"` source, targeting the exact field that chart itself binds
   the filter to (per its own `parameter_mappings` — not assumed to match
   a sibling chart's binding).
3. **Every field passed through in step 1 or 2 is also a visible column**
   on the destination (in the breakout and left `enabled: true` in
   `table.columns`) — never a silent filter target with nothing shown for
   it, per "Every dashboard filter passed into a drill-down must also be a
   visible column on it" above.
4. **Entity profile links** are used in place of the bare name column for
   every candidate/company/job/contact name displayed — not the plain
   text name.
5. **At least one genuinely useful, independently-actionable context
   field** (e.g. `email` for a candidate list) is present — not just the
   mechanical minimum needed to answer the metric.
6. **If the metric is a distinct-count aggregation**, the drill-down groups
   by every displayed column *plus* the entity id, not just the visible
   columns.
7. **A filtered-slice spot-check was actually run and matched** the
   report's own cell for that slice — not just eyeballed.

Report the audit as part of finishing the drill-down step (e.g. "audited
all N drill-downs against the checklist — found and fixed one gap: X"),
not silently — the same "say what was checked" norm as any other
validation step in this project.
