# Chart generation

Goal: turn a confirmed recommendation into a real Metabase card via `mb`,
using only fields that were actually discovered — never assumed schema.

## Sequence (do not skip steps)

1. Analysis and recommendation are already done (`prompts/analysis.md`,
   `prompts/recommendation.md`).
2. **Ask for confirmation** on which recommendation(s) to actually create,
   unless the user already said "create all of them" or similar.
3. Build the query:
   - **GUI/MBQL first, always.** Every chart must be built through Metabase's
     visual query builder (MBQL — load the `mbql` skill) by default. Only
     fall back to native SQL (load `native-sql`) when the required logic
     genuinely cannot be expressed in MBQL (e.g. the stage-ordinal `CASE`
     ranking from CLAUDE.md's "current pipeline stage" rule, window
     functions, or other computations the GUI builder can't represent). If
     you fall back to SQL, state explicitly why MBQL wasn't sufficient.
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
4. Choose the visualization (load the `visualization` skill for `display`
   and `visualization_settings` conventions):
   - Match chart type to the insight and data shape (see `Chart Type` chosen
     in the recommendation) — funnel for stage drop-off, line/area for
     trends over time, bar/stacked-bar for categorical comparisons, table
     for a list-style finding (e.g., "which jobs"), KPI for a single number.
   - Keep it understandable to a business user: clear title, sensible axis
     labels, no unnecessary complexity.
5. Resolve the destination collection — see CLAUDE.md "Where created charts
   live": the account's sub-collection under collection 199 ("Data Team
   WIP"), creating it if it doesn't exist yet.
6. Create the card:

```bash
mb card create --file ./.scratch/<name>.json --profile <profile> --json
```

Include a meaningful `name`, the validated `dataset_query`, chosen `display`,
minimal sensible `visualization_settings`, and `collection_id` set to the
resolved account collection. Add filters from the recommendation's
"Recommended Filters" as query filters or dashboard-ready parameters where
appropriate.

7. **Verify** the created card:

```bash
mb card get <card-id> --json
```

Confirm it matches what was intended (query, display, name, collection).

8. Report back to the user: card id, name, chart type, and how to find it in
   Metabase (collection it landed in). Do not claim success without having
   run step 7.
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
- Don't duplicate an existing card/dashboard (re-check per CLAUDE.md
  "Avoiding duplicate charts") unless justified, and say why.
- Never delete, archive, or modify a pre-existing card, dashboard, or
  collection — only ever add new content (see CLAUDE.md hard constraint 7).
  Archiving is only ever acceptable on a card this same operation just
  created (e.g. cleaning up after a failed validation), never on anything
  that already existed before this session touched it.
