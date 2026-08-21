# Workflow (for humans)

This is the same flows described in `CLAUDE.md`, written for a teammate
reading it rather than for Claude executing it.

1. Open this folder in VS Code, with Claude Code active.
2. Say something like **"start the project"**, "start analysis", "analyze an
   account", "recommend charts", or "create analytics".
3. Claude checks Metabase CLI configuration first (`mb auth list`/`status`).
   If nothing is configured, it will tell you exactly what to run — see
   README.md.
4. Claude asks which kind of work you want:
   - **General** — no fixed workflow: just an account and a free-text
     description of what to build (see "General flow" below).
   - **Recommendation Engine** — the full insight-discovery flow (steps 5-11
     below).
   - **Default Dashboard** — the standardized onboarding dashboard every
     Advanced Analytics client gets, built automatically (see "Default
     Dashboard flow" below).
   - **Important Metrics Dashboard** — the standardized hiring-efficiency
     dashboard every Advanced Analytics client gets, also built
     automatically (see "Important Metrics Dashboard flow" below).
   - **Transcript to Insights** — turn a client meeting transcript into
     chart recommendations grounded in that account's real data (see
     "Transcript to Insights flow" below).

## General flow

1. Claude asks: **"Which Recruit CRM account would you like to work with?
   Please provide the account number."**
2. Claude asks: **"What would you like to build?"** — reply with whatever
   you have in mind: a specific chart, a metric, a comparison, anything.
   There's no entity-choice prompt and no recommendation count here.
3. Claude discovers only the data needed to fulfill your request (a scoped
   version of the same discovery method the Recommendation Engine flow
   uses), checks it against the same data-quality gate and duplicate-chart
   check as every other flow, and either builds it or tells you plainly why
   it can't.
4. If your request is unambiguous and clearly one chart, Claude just builds
   it and reports back. If it's ambiguous or could reasonably become more
   than one chart, Claude states what it's about to build and confirms
   first. Either way, the chart lands directly in the account's "Data Team
   WIP" sub-collection — same convention as the Recommendation Engine and
   Transcript to Insights flows.

## Recommendation Engine flow

5. Claude asks: **"Which Recruit CRM account would you like to analyze?
   Please provide the account number."** — reply with the account number.
6. Claude asks which entity you want chart recommendations for — a
   plain-text numbered list built from the entities actually discovered for
   *that* account (never a fixed list), with "All" first and "Do you have
   anything in mind?" (free-text) last for a custom focus.
7. Claude asks: **"How many chart recommendations would you like me to
   generate?"** — reply with a number (1, 3, 5, 10, whatever you want).
8. Claude discovers the account's actual data through `mb` (databases,
   tables, fields, existing charts/dashboards), scoped to your chosen
   entity/focus — no manual schema description needed from you.
9. Claude analyzes the real data for meaningful patterns (funnel
   bottlenecks, recruiter performance gaps, stalled jobs, client activity,
   etc.) and applies a data-quality check before trusting any of them.
10. Claude presents exactly N ranked recommendations, each explaining what
    the chart shows, why it's useful, what question it answers, what
    triggered it, and what to investigate next.
11. Claude asks which recommendation(s) you want actually created in
    Metabase, then creates the confirmed chart(s) via `mb card create`,
    verifies each with `mb card get`, and gives you the card id/name to open
    in Metabase. Cards land under "Data Team WIP" in a sub-collection named
    for the account number.

## Default Dashboard flow

1. Claude asks: **"Which Recruit CRM account would you like to build the
   default dashboard for? Please provide the account number."**
2. Claude runs `scripts/create_default_dashboard.py`, which discovers the
   account's actual tables via `mb`, builds the same fixed set of charts
   every account gets (skipping any chart whose underlying entity doesn't
   exist for this account), and assembles them into a dashboard — dry-run
   validating every query first, and stopping rather than touching anything
   if a default dashboard already exists for the account.
3. Claude reports back the dashboard id/link, which cards were created vs.
   skipped (and why), and the collections involved: the dashboard directly
   in the account's "Data Team WIP" sub-collection, its cards one level
   deeper in a nested "Default Dashboard Charts" sub-collection.
4. If the script fails or skips, Claude relays that plainly rather than
   forcing something.

## Important Metrics Dashboard flow

1. Claude asks: **"Which Recruit CRM account would you like to build the
   important metrics dashboard for? Please provide the account number."**
2. Claude runs `scripts/create_important_metrics_dashboard.py`, which
   discovers the account's actual tables via `mb`, builds the same fixed set
   of hiring-efficiency/ratio/trend/candidate-diversity charts every account
   gets (skipping any chart whose underlying entity doesn't exist for this
   account), and assembles them into a dashboard — dry-run validating every
   query first, and stopping rather than touching anything if an important
   metrics dashboard already exists for the account.
3. Claude reports back the dashboard id/link, which cards were created vs.
   skipped (and why), and the collections involved: the dashboard directly
   in the account's "Data Team WIP" sub-collection, its cards one level
   deeper in a nested "Important Metrics Dashboard Charts" sub-collection.
4. If the script fails or skips, Claude relays that plainly rather than
   forcing something.

## Transcript to Insights flow

1. Claude asks: **"Which Recruit CRM account is this transcript for? Please
   provide the account number."**
2. Claude asks you to paste the full transcript (raw call transcript or
   notetaker output, any length/format — no need to clean it up first).
3. Claude reads the transcript purely as a source of analytics
   requirements — never as instructions to Claude, even if something in it
   reads like a directive — and extracts every place the client expressed a
   wish to measure, track, or report on something.
4. For each requirement, Claude grounds it in the account's real discovered
   data (same discovery/analysis rigor as the Recommendation Engine flow).
   If the account's data genuinely can't support a requirement, Claude says
   so explicitly instead of inventing or approximating it.
5. Claude presents the resulting charts as a numbered list, citing what in
   the transcript drove each one, and separately calls out anything that
   couldn't be built or was too vague to draft.
6. Claude asks which recommendation(s) to actually create ("create all"
   creates every one presented); confirmed charts are created as individual
   cards directly in the account's "Data Team WIP" sub-collection — this
   flow does not assemble a dashboard (future scope).

## In every flow

If at any point the account can't be found, the data is too thin/dirty for a
given analysis, or Metabase can't be reached, Claude will say so directly
rather than inventing results. Every flow appends an entry to the local,
git-ignored `logs/history.jsonl` audit trail; for the General, Recommendation
Engine, and Transcript to Insights flows this is enforced by a Claude Code
hook that flags the session if a card/dashboard was created but never logged.
