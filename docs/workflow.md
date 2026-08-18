# Workflow (for humans)

This is the same flow described in `CLAUDE.md`, written for a teammate
reading it rather than for Claude executing it.

1. Open this folder in VS Code, with Claude Code active.
2. Say something like **"start the project"**, "start analysis", "analyze an
   account", "recommend charts", or "create analytics".
3. Claude checks Metabase CLI configuration first (`mb auth list`/`status`).
   If nothing is configured, it will tell you exactly what to run — see
   README.md.
4. Claude asks: **"Which Recruit CRM account would you like to analyze?
   Please provide the account number."** — reply with the account number.
5. Claude asks: **"How many chart recommendations would you like me to
   generate?"** — reply with a number (1, 3, 5, 10, whatever you want).
6. Claude discovers the account's actual data through `mb` (databases,
   tables, fields, existing charts/dashboards) — no manual schema
   description needed from you.
7. Claude analyzes the real data for meaningful patterns (funnel
   bottlenecks, recruiter performance gaps, stalled jobs, client activity,
   etc.) and applies a data-quality check before trusting any of them.
8. Claude presents exactly N ranked recommendations, each explaining what the
   chart shows, why it's useful, what question it answers, what triggered
   it, and what to investigate next.
9. Claude asks which recommendation(s) you want actually created in
   Metabase.
10. Claude creates the confirmed chart(s) via `mb card create`, verifies each
    with `mb card get`, and gives you the card id/name to open in Metabase.

If at any point the account can't be found, the data is too thin/dirty for a
given analysis, or Metabase can't be reached, Claude will say so directly
rather than inventing results.
