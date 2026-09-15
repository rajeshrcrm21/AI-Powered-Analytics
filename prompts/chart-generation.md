# Chart generation

Goal: turn a confirmed recommendation into a real Metabase card via `mb`,
using only fields that were actually discovered — never assumed schema.

## Sequence (do not skip steps)

1. The candidate chart(s) have already been presented and explained — see
   `prompts/requirements-intake.md`.
2. **Ask for confirmation** on which recommendation(s) to actually create,
   unless the user already said "create all of them" or similar. In the
   same turn, **also ask whether to add a description to the card(s)**
   being created (e.g. "Would you like a short description added to the
   chart(s) being created?" — a plain yes/no, per CLAUDE.md "Chart
   creation"). Default is **no description** — only add one if the user
   says yes.
3. Build the query:
   - **GUI/MBQL first, always.** Every chart must be built through Metabase's
     visual query builder (MBQL — load the `mbql` skill) by default. Only
     fall back to native SQL (load `native-sql`) when the required logic
     genuinely cannot be expressed in MBQL (e.g. the stage-ordinal `CASE`
     ranking from CLAUDE.md's "current pipeline stage" rule, window
     functions, or other computations the GUI builder can't represent). If
     you fall back to SQL, state explicitly why MBQL wasn't sufficient, and
     save it as a Model first rather than a one-off raw-SQL question — build
     the actual chart on top of the Model in the GUI (see CLAUDE.md "Chart
     creation" for when a Model is/isn't worth it vs. clutter).
   - **A stage-to-stage conversion ratio (e.g. 2nd Interview → Final
     Interview) is not a naive `COUNT(B)/COUNT(A)`** — build it as the
     double summarization in CLAUDE.md's "Stage-to-stage conversion ratios"
     (one row per id per stage reached → filter to the earlier stage's ids →
     summarize again for the later stage among just those). This is usually
     buildable in the GUI as two chained summarize steps, no SQL needed.
   - **Any average, ratio, rate, or other calculation built from more than
     one raw aggregate must be split into separate, explicitly-named
     steps** — see CLAUDE.md "Query transparency". Give each intermediate
     aggregation/custom column a clear `name`/`display-name` (e.g. "Sum of
     Deal Value", "Deal Count", then "Average Deal Value" as the final
     division) so a teammate opening the notebook editor can read the
     calculation directly from the query, step by step — never a single
     unnamed expression, and never explained instead in the card's
     `description` (that field is client-facing only — see CLAUDE.md).
   - **A join never gets a custom/friendly alias** — see CLAUDE.md "Query
     transparency" ("Join aliases"). Use the real, account-suffixed table
     name being joined (e.g. `assign_job_candidate_662`) as the join's
     alias, not a made-up display name — otherwise a teammate opening the
     notebook editor later sees a label that doesn't match the schema and
     can't tell which table it actually points to.
   - **No filter or condition that changes the result may be buried where
     the notebook GUI won't show it** — see CLAUDE.md "Query transparency".
     A join's `conditions` holds only the join key(s), never an extra
     restriction (e.g. `AND deal_stage = 'Won'`) — pull anything like that
     out into its own visible Filter step instead. If the query is built on
     a Model, that's fine per the Model guidance above, but the Model must
     itself be clearly named/described (for teammates, not the client) and
     — per step 8 below — its use must be named out loud when the chart is
     reported back, not left implicit.
   - Use only tables/fields confirmed to exist during discovery.
   - **Validate before creating — native SQL needs *more* rigor than MBQL,
     not less**, since it bypasses the query builder's structural guardrails
     entirely (no typo-checked column/table refs, no join validation) and is
     exactly the path used for the more error-prone queries (stage-ordinal
     `CASE` ranking, window functions):
     1. `mb query --dry-run` first, always, for every query — MBQL or
        native SQL. This pre-flight-validates the query envelope (shape,
        template tags, parameter refs) for both.
     2. For native SQL specifically, a clean dry-run is **not enough on its
        own** — it cannot check the SQL text itself. Follow it with an
        actual `mb query --file ... --json` run (no `--dry-run`) against
        the real warehouse, and confirm it genuinely succeeded (no error,
        a sane column count and row shape for what the chart needs) before
        creating the card. Never create a native-SQL card off a dry-run
        alone.
     3. **This run is the one and only point in the entire workflow that
        touches real row data.** Discovery and resolution (`prompts/
        discovery.md`, `prompts/requirements-intake.md`) never sample field
        values or run exploratory queries — they work from schema metadata
        and user-confirmed definitions only. So this is also where a
        definitional assumption that doesn't hold (e.g. an "at-risk deals"
        requirement built on a "Lost" stage this account has none of) or an
        unrecognized category literal actually surfaces — empty results or
        an error here, not a separate live check run earlier. If that
        happens, stop and follow `prompts/infeasible-requirement.md` instead
        of forcing the card through.
4. Choose the visualization (load the `visualization` skill for `display`
   and `visualization_settings` conventions):
   - Match chart type to the insight and data shape (see `Chart Type` chosen
     in the recommendation) — funnel for stage drop-off, line/area for
     trends over time, bar/stacked-bar for categorical comparisons, table
     for a list-style finding (e.g., "which jobs"), KPI for a single number.
   - Keep it understandable to a business user: clear title, sensible axis
     labels, no unnecessary complexity.
   - **Format every value with its actual unit** — see CLAUDE.md "Value
     formatting" and `config/analysis-config.md`'s table of which field
     shapes are monetary vs. percent vs. duration vs. a plain count. A
     monetary field is never formatted with an assumed symbol: if this
     account's currency isn't already recorded in
     `references/metric-glossary.md`, ask the user once (e.g. "Which
     currency should chart values use for this account — USD, EUR, GBP,
     INR, or another?") before creating the card, then **write the answer
     to that account's `## Account <n>` section immediately — in the same
     turn as the answer, before creating the card** — so later charts in
     this session and future sessions don't re-ask. Don't defer this to a
     later cleanup step; it's the whole reason "ask once per account" works.
   - **Show the value on every point/bar/segment by default** — see
     CLAUDE.md "Data labels": `"graph.show_values": true` for bar/line/
     area/row/combo/funnel, `"pie.percent_visibility": "inside"` or
     `"both"` for pie. Tables, pivots, and scalar/smartscalar/progress KPIs
     already show the value directly — nothing to add there.
   - **Combo chart with a mix of series types (e.g. a per-category
     breakdown plus a total/summary line): set `series_settings.<key>.display`
     explicitly for every series, not just the one that needs to differ from
     Metabase's default** — see CLAUDE.md "Combo chart series display" for
     why leaving any series unset is never safe here.
5. Resolve the destination collection — see CLAUDE.md "Where created charts
   live": whichever convention Requirements Intake's step 2 settled on for
   this request — the account's sub-collection under collection 199 ("Data
   Team WIP"), or the "<Dashboard Name> Cards" sub-collection under the
   account's own collection's **Cards** folder — creating whichever
   collections in the chain don't exist yet.
6. Create the card:

```bash
mb card create --file ./.scratch/<name>.json --profile <profile> --json
```

Include a meaningful `name`, the validated `dataset_query`, chosen `display`,
minimal sensible `visualization_settings`, and `collection_id` set to the
resolved destination collection from step 5. Add filters from the
recommendation's "Recommended Filters" as query filters or dashboard-ready
parameters where appropriate. Only include a `description` if the user
opted in at step 2 — when they didn't, omit the field entirely rather than
adding one anyway.

7. **Verify** the created card:

```bash
mb card get <card-id> --json
```

Confirm it matches what was intended (query, display, name, collection).

8. Report back to the user: card id, name, chart type, and how to find it in
   Metabase (collection it landed in). Do not claim success without having
   run step 7. **If the chart is built on top of a Model**, name the Model
   and summarize in one line what logic it applies (e.g. "built on Model
   'Current Pipeline Stage', which ranks each candidate-job pair's stages
   and keeps the furthest one reached") — see CLAUDE.md "Query
   transparency". That dependency is never left for the user to notice on
   their own.
9. Append one `chart_created` entry to `logs/history.jsonl` for this card
   (see CLAUDE.md "History log" for the exact schema).

## If creation isn't possible

If a required field/table isn't available, or the query can't be validated,
explain specifically why (missing field, insufficient permissions, etc.) and
move to the next-ranked recommendation instead of forcing a broken chart.

## Guardrails

- Never create more cards than the user confirmed.
- Never invent field names — if unsure a field exists, re-check with
  `mb table fields <id>` rather than guessing.
- When the source material (user message, transcript, shared sheet) names
  the specific field a business term maps to, use that field — don't
  substitute a same-sounding field picked by name/type matching or data
  completeness instead (see CLAUDE.md "Data discovery").
- Don't duplicate an existing card/dashboard (re-check per CLAUDE.md
  "Avoiding duplicate charts") unless justified, and say why.
- Never delete, archive, or modify a pre-existing card, dashboard, or
  collection — only ever add new content (see CLAUDE.md hard constraint 7).
  Archiving is only ever acceptable on a card this same operation just
  created (e.g. cleaning up after a failed validation), never on anything
  that already existed before this session touched it.
- Never add a `description` to a card unless the user explicitly opted in
  when asked at step 2 — no description is the default. When one is added,
  it's client-facing (what the chart shows, why it matters) — never a
  formula, calculation, or query-logic explanation. If the calculation
  isn't clear on its own, that means the query's aggregation/custom-column
  steps need clearer names, not a longer description (see CLAUDE.md "Query
  transparency").
