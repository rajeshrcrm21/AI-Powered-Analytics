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
   - **Requirements Intake** — you state chart requirements directly (a
     single ask, a numbered list, a pasted client doc) rather than a
     transcript, and Claude grounds each in that account's real data (see
     "Requirements Intake flow" below). This is the project's primary flow.
   - **Transcript to Insights** — turn a client meeting transcript into
     chart recommendations grounded in that account's real data (see
     "Transcript to Insights flow" below).

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
   data, using the same metadata-only discovery as the Requirements Intake
   flow. If the account's data genuinely can't support a requirement, Claude
   says so explicitly instead of inventing or approximating it.
5. Claude presents the resulting charts as a numbered list, citing what in
   the transcript drove each one, and separately calls out anything that
   couldn't be built or was too vague to draft.
6. Claude asks which recommendation(s) to actually create ("create all"
   creates every one presented); confirmed charts are created as individual
   cards directly in the account's "Data Team WIP" sub-collection — this
   flow does not assemble a dashboard (future scope).

## Requirements Intake flow

1. Claude asks: **"Which Recruit CRM account are these requirements for?
   Please provide the account number."**
2. Claude asks you to share your chart requirements — a single ask, a
   numbered list, or a pasted client doc listing several. Any format is
   fine.
3. For each requirement, Claude checks for a known chart pattern or
   reference material first (`references/canonical-patterns.md` if it
   exists, `references/schema-map.md`, `references/metric-glossary.md`),
   then falls back to live discovery against the account's real data — full
   rigor, no shortcuts. If the data genuinely can't support a requirement,
   Claude says so instead of inventing it.
4. Claude asks a clarifying question only when a requirement is genuinely
   ambiguous in a way that changes the query — never a generic "can you
   clarify?"
5. Claude presents the resulting charts as a numbered list, citing which
   requirement drove each one, and separately calls out anything that
   couldn't be built.
6. Claude asks which recommendation(s) to actually create ("create all"
   creates every one presented); confirmed charts are created as individual
   cards directly in the account's "Data Team WIP" sub-collection — this
   flow does not assemble a dashboard.

## In every flow

If at any point the account can't be found, the data is too thin/dirty for a
given analysis, or Metabase can't be reached, Claude will say so directly
rather than inventing results. Every flow appends an entry to the local,
git-ignored `logs/history.jsonl` audit trail; a Claude Code hook enforces
this whenever a card/dashboard is created directly via `mb`
by flagging the session if one was created but never logged.
