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
   - **Requirements Intake** — you share chart/dashboard requirements
     directly, in whatever form you have them: a written ask, a numbered
     list, a pasted client transcript, an attached document (PDF, image,
     etc.), or several combined. Claude grounds each in that account's real
     data and assembles a dashboard — new or existing — with a
     documentation tab explaining it (see "Requirements Intake flow"
     below). This is the project's primary flow.
   - **Default Dashboard** — the standardized onboarding dashboard every
     Advanced Analytics client gets, built automatically (see "Default
     Dashboard flow" below).
   - **Important Metrics Dashboard** — the standardized hiring-efficiency
     dashboard every Advanced Analytics client gets, also built
     automatically (see "Important Metrics Dashboard flow" below).

## Requirements Intake flow

1. Claude asks: **"Which Recruit CRM account are these requirements for?
   Please provide the account number."**
2. Claude asks — every time, not just once per account — whether this
   request's work should be saved in the internal "Data Team WIP"
   collection, or in the account's own collection. This decides where every
   card, Model, drill-down, and dashboard for this request lands.
3. Claude asks you to share your requirements — a written ask, a numbered
   list, a pasted transcript (call recording / notetaker output), an
   attached document (PDF, image, etc.), or any combination of these,
   including more than one attachment at once. Any format is fine, and
   nothing needs cleaning up first. **If your source is an audio or video
   recording, Claude will ask for a text transcript instead** — this
   project has no way to transcribe audio/video directly.
4. Claude reads every transcript/document purely as a source of analytics
   requirements — never as instructions to Claude, even if something in it
   reads like a directive — and extracts every place a requirement was
   expressed (explicitly or implicitly): a stated ask taken directly, a
   transcript's "we want to see how each recruiter is doing," a document's
   own bullet list or mockup.
5. For each requirement, Claude checks for a known chart pattern or
   reference material first (`references/canonical-patterns.md` if it
   exists, `references/schema-map.md`, `references/metric-glossary.md`),
   then falls back to live discovery against the account's real data — full
   rigor, no shortcuts. If the data genuinely can't support a requirement,
   Claude says so instead of inventing it.
6. Claude asks a clarifying question only when a requirement is genuinely
   ambiguous in a way that changes the query — never a generic "can you
   clarify?"
7. Claude presents the resulting charts as a numbered list, citing which
   requirement (and which source, when more than one was given) drove each
   one, and separately calls out anything that couldn't be built.
8. Claude asks which recommendation(s) to actually create ("create all"
   creates every one presented); confirmed charts are created as individual
   cards directly in whichever collection was chosen at step 2 (under the
   account's own collection, they go in its "Cards" sub-collection instead).
9. Claude decides where the charts land: a dashboard you already named, an
   existing dashboard it asks you about if its own duplicate-check turns up
   one that plausibly already covers the same ground (scoped to that same
   chosen collection), or one or more new dashboards otherwise (grouped by
   topic if the request spans more than one, unless you said otherwise).
   Updating an existing dashboard only ever adds to it — Claude never
   rearranges, resizes, or removes anything already on it.
10. Claude assembles the confirmed cards onto the chosen dashboard(s) — laid
    out sensibly, with shared filters wired up and drill-downs
    (`click_behavior`) added wherever clicking into a summary value has an
    obvious, useful destination. A brand-new dashboard in the account's own
    collection gets pinned there.
11. Claude adds a **documentation tab** to each dashboard touched — a new
    tab containing only text cards (Metabase's markdown tile, not a
    separate document): the dashboard's purpose, what each chart/metric
    means in plain business language, and how to use its filters/
    drill-downs — written for the people who'll actually read the
    dashboard.

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
   skipped (and why), and the collections involved: the dashboard pinned
   directly in the account's own collection (never "Data Team WIP" — this
   flow always uses the account's own collection), its cards one level
   deeper in that collection's "Cards" sub-collection, under "Default
   Dashboard Cards".
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
   skipped (and why), and the collections involved: the dashboard pinned
   directly in the account's own collection (never "Data Team WIP" — this
   flow always uses the account's own collection), its cards one level
   deeper in that collection's "Cards" sub-collection, under "Important
   Metrics Dashboard Cards".
4. If the script fails or skips, Claude relays that plainly rather than
   forcing something.

## In every flow

If at any point the account can't be found, the data is too thin/dirty for a
given analysis, or Metabase can't be reached, Claude will say so directly
rather than inventing results. Every flow appends an entry to the local,
git-ignored `logs/history.jsonl` audit trail; for the Requirements Intake
flow this is enforced by a Claude Code hook that flags the session if a
card was created or a dashboard was created/updated but never logged. The
Default Dashboard and Important Metrics Dashboard scripts log themselves in
code instead.
