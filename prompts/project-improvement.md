# Project improvement review

A **separate, on-demand review — not an automatic step that runs after
every task.** Only run this when the user explicitly asks for it (e.g.
"any project improvement ideas?", "suggest an improvement", "review the
backlog"). Produce a short, concrete suggestion for improving the project
itself: `prompts/`, `references/`, `scripts/`, `config/`, or CLAUDE.md's
own guardrails.

This exists to turn what sessions actually run into over time into a
standing backlog this project can act on later — not a pleasantry recited
out of habit. A suggestion that's said once in chat and never logged is
lost the moment the conversation ends; logging it (see "Log it" below) is
what makes it something the project can actually be built from, session
over session, instead of re-discovering the same rough edge repeatedly.

## Ground it in the project's own files, not the conversation

This review is a different kind of check from CLAUDE.md's automatic
"Closing every task: suggest a project improvement" step, and the two must
not blur together:

- **CLAUDE.md's closing step** runs after every task and is grounded in
  whatever that specific task just surfaced in this conversation — a live
  observation about the work just done, tied to that session's context.
- **This review** is invoked deliberately, on its own, and is **never**
  grounded in conversation context — not the current session's task, not
  what was just built, not "recent activity." Even when it happens to be
  asked right after finishing something in the same conversation, don't
  base the suggestion on that task — that's the closing step's job, not
  this one's.

Instead, base every suggestion here on an actual pass over the **project
repository itself**: (re-)read `CLAUDE.md` in full and check it against
`prompts/`, `references/`, `scripts/`, and `config/` for a real gap,
contradiction, drift, or missed opportunity — e.g. a rule CLAUDE.md states
that a script doesn't actually implement, two files describing the same
convention slightly differently, a `references/*.md` entry that's gone
stale against what a script or prompt now does, or a script whose
docstring no longer matches its own behavior. `logs/history.jsonl` and the
existing entries in `references/project-improvements.md` are fair
evidence to pull into that pass (what's actually been built/skipped, what
patterns keep recurring, what's already been flagged) — but they're one
input into a repo-wide check, never a substitute for actually reading the
files as they stand today, and never the sole basis for a suggestion on
their own.

Never invent a suggestion from first principles without having actually
looked at the current contents of the file(s) it's about.

Once grounded, draw from whichever of these genuinely applies:

- **Robustness / production-grade**: a guardrail a script or prompt works
  around instead of fixing at the source, a footgun recorded in
  `logs/history.jsonl` that cost real back-and-forth to diagnose but was
  never promoted into its own "Known Metabase gotchas" entry in
  `prompts/drilldowns.md`, or a validation step this project's
  prompts/scripts don't yet have but should.
- **Better alternatives**: a different Metabase feature, MBQL pattern,
  chart type, or way of structuring a request that would have gotten a
  cleaner result than the pattern a script or `references/canonical-patterns.md`
  currently encodes.
- **Consistency**: naming, collection layout, or a convention that drifted
  between two accounts' recorded conventions, or between what
  `logs/history.jsonl` shows was actually built and what `references/*.md`
  documents.
- **Architecture**: how `prompts/`, `references/`, `scripts/`, `config/`,
  and `logs/` fit together — a manual step that could become a script, a
  reference file missing an account's recorded convention, a guardrail
  that should move between a script and CLAUDE.md.
- **Time/token efficiency without losing context**: a way the discovery →
  build → verify loop could reach the same correct result with fewer `mb`
  round-trips or less redundant live-value querying, or better reuse of
  already-recorded `references/canonical-patterns.md` /
  `references/schema-map.md` / `references/metric-glossary.md` entries
  instead of re-deriving or re-asking what this project already knows.
- **Core-function quality**: anything that would make the charts/dashboards
  this project produces more professional, functional, well-optimized, or
  accurate — sharper drill-downs, better use of filters, cross-filtering,
  tabs, or other Metabase-native capability this project isn't yet using
  well.
- **Workflow friction**: a rough edge in Requirements Intake, Default
  Dashboard, or Important Metrics Dashboard — a question asked too often, a
  step that could be inferred instead of asked, a gate redundant with one
  earlier in the same flow.

## Say it

Keep it to one to three sentences unless the user asks to go deeper — a
pointer, not a proposal document. Frame it as a suggestion or question,
never as an action already taken: acting on it is a separate, explicitly
confirmed step, exactly like any other change to this project's own files
(see CLAUDE.md's "Executing actions with care" norms — this project's own
`prompts/`, `references/`, `scripts/`, and `CLAUDE.md` are files too).

It's fine to say there's genuinely nothing worth flagging (e.g. recent
work was routine and no real pattern turned up) — don't manufacture a
suggestion to satisfy the request, and don't log anything in that case.

## Log it

When a suggestion is actually given (not skipped), append one entry to
`references/project-improvements.md`'s **Open** section. Unlike
`logs/history.jsonl`, this file is **committed and shared** — the whole
point is that a rough edge one teammate's session hits becomes visible to
the whole team, not just logged locally where nobody else will ever see
it. Append under the `<!-- Append new suggestions below this line -->`
marker, oldest first, one entry in this exact shape:

```markdown
- 2026-08-19 — account 662 — workflow-friction — Requirements Intake, recruiter performance dashboard
  The currency question gets asked even when every chart in the request is
  a plain count — worth skipping it until a monetary field is actually
  about to be formatted.
```

- **Date**: real wall-clock date (`TZ="Asia/Kolkata" date +"%Y-%m-%d"` —
  same source of truth as CLAUDE.md "History log", date only, no time
  needed for a backlog entry).
- **Account**: the account this task was for, or `general` for a task not
  tied to one (e.g. a cross-account `mb` lookup, or a suggestion about the
  project's own files).
- **Category**: one of the seven bullets above, kebab-cased
  (`robustness`, `better-alternatives`, `consistency`, `architecture`,
  `time-token-efficiency`, `core-function-quality`, `workflow-friction`).
- **Task**: one short phrase naming what was being done when this
  surfaced.
- **Body** (indented line below): the exact suggestion as said to the
  user — don't paraphrase a second version for the log.

Never move an entry to **Resolved** yourself just because you logged it —
that only happens once the suggestion has actually been acted on (or
explicitly declined) as its own separate, confirmed change, per this
file's own instructions.

This file is the backlog: periodically reviewing it (the user, or a future
session asked to do so) is how a recurring pattern turns into an actual
change to `prompts/`, `references/`, `scripts/`, or CLAUDE.md — the same
explicitly-confirmed way any other change to this project's own files
gets made, never acted on silently just because it was logged.
