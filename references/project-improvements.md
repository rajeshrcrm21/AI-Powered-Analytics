# Project improvement backlog

Suggestions surfaced while doing real work in this project — one entry per
task, per `prompts/project-improvement.md`'s "Log it" step. **Committed
and shared**, unlike `logs/history.jsonl` (which is local-only,
git-ignored, per-machine): the point of this file is that a rough edge one
teammate's session hits becomes visible to everyone, not just rediscovered
independently session after session.

This is a backlog, not a changelog — an entry landing here is not itself
an action taken. Turning one into a real change to `prompts/`,
`references/`, `scripts/`, or `CLAUDE.md` is a separate, explicitly
confirmed step, exactly like any other change to this project's own files.

Append new entries under **Open**, oldest first. When an entry is acted on
(or deliberately declined), move it to **Resolved** with a one-line note
on what changed (or why it was declined) and the date.

## Open

<!-- Append new suggestions below this line, one entry per task:

- 2026-08-19 — account 662 — workflow-friction — Requirements Intake, recruiter performance dashboard
  The currency question gets asked even when every chart in the request is
  a plain count — worth skipping it until a monetary field is actually
  about to be formatted.
-->

## Resolved

- 2026-09-15 — general — robustness — Project improvement review (grounded in account 44663's Sourcing Report drill-down history)
  Mid-session on 44663, `mb card query --parameters` returned a negative result for a plain-MBQL custom-destination drill-down, which was read as "this whole mechanism doesn't work" and triggered a full rebuild (native SQL, then an alternate on-dashboard Detail-tab-with-parameter_mappings architecture) before a real UI-built example proved the original plain-MBQL `click_behavior` approach was fine all along. The actual cause — `mb card query --parameters` doesn't exercise the same code path as real click-through navigation — is stated once in `logs/history.jsonl` but isn't in `prompts/drilldowns.md`'s "Known Metabase gotchas" list. Worth adding as its own bullet there: a negative result from that command is not proof a click_behavior mechanism is broken, so don't let it justify an architecture rebuild — check against a confirmed UI-built example first, per the gotcha bullet already there for guessing the shape itself wrong.
  → Resolved 2026-09-15: added this as its own "Known Metabase gotchas" bullet in `prompts/drilldowns.md`, right after the "guessed wrong twice" bullet it builds on.

- 2026-09-15 — general — robustness — Project improvement review (grounded in account 44663's recent drill-down history)
  Three separate follow-up sessions each fixed a different completeness gap in the same dashboard's drill-downs after the fact (a missing breakout dimension in click_behavior, a filter-bound field left invisible, no independently-actionable context field) — all against rules already documented at the time.
  → Resolved 2026-09-15: added a "Completion audit" section to `prompts/drilldowns.md` (a 7-point checklist run once after wiring a batch, before reporting it done) and a corresponding required bullet in CLAUDE.md's condensed "Drill-downs" section.

- 2026-09-15 — general — consistency — Project improvement review (grounded in references/metric-glossary.md)
  metric-glossary.md's "Term mappings (this account only)" section is one flat, unlabeled list, but it already holds mappings from at least two different accounts (a 662-context set plus an explicit `assign_job_candidate_53181` entry) with nothing marking which account each mapping belongs to — a future session on a different account could mistake one account's stage/field mapping as its own. Worth restructuring the file into per-account sections (e.g. a `## Account <n>` heading per account) so CLAUDE.md's "never carry a mapping forward from one account to another" rule is actually enforceable by the file's own shape, not just by convention.
  → Resolved 2026-09-15: restructured `references/metric-glossary.md` into an account-agnostic "Open questions (template)" section plus `## Account <n>` sections for confirmed per-account answers. Only the `assign_job_candidate_53181` mapping had a recoverable account number, so it stayed flagged for a future move into its own `## Account 53181` section; every other prior mapping (no recoverable account) moved to a clearly-labeled "Unattributed" section that must not be reused for any specific account without reconfirming with the user.

- 2026-09-15 — general — consistency — Project improvement review (grounded in references/metric-glossary.md and logs/history.jsonl)
  `logs/history.jsonl` shows real chart/dashboard work across at least 10 distinct accounts (662, 2227, 6268, 34301, 43720, 51254, 62956, 80402, 44663, 38992, plus 92840 and 96467 appearing elsewhere), yet `references/metric-glossary.md` has zero populated `## Account <n>` sections — only the illustrative "Account 662" template example and legacy pre-restructure "Unattributed" entries. Since CLAUDE.md/discovery.md/requirements-intake.md all instruct recording a confirmed answer (currency, hiring-stage order, term mapping) back to this file the first time it's resolved for an account, this gap suggests those confirmed answers are being resolved in-session but never written back — so the "ask once per account" design is silently failing and each new session likely re-asks a question a prior session already got answered.
  → Resolved 2026-09-15: tightened the write-back instruction everywhere a business-term/definitional answer gets confirmed — CLAUDE.md ("Data discovery", "Value formatting", and the hiring-stage-order paragraph), `prompts/discovery.md` section 4, `prompts/chart-generation.md`'s currency step, and `prompts/requirements-intake.md`'s term-mismatch step — from "record the answer" (a deferrable-sounding instruction) to "write it immediately, in the same turn it's confirmed, before moving on." Whether this actually closes the gap (vs. sessions still not doing it) needs checking against a future account's actual glossary section once one goes through the flow again.
  (An initial version of this fix also told live discovery to auto-append new structural facts to `references/schema-map.md` the moment it found them. Corrected 2026-09-15, same day: `schema-map.md` is deliberately stable and manually curated — its per-account write-once treatment doesn't apply there. Discovery now flags a structural discrepancy to the user instead of writing it in; a confirmed schema change reaches the file only as its own separate, reviewed edit.)

- 2026-08-19 — account 662 — workflow-friction — Requirements Intake, recruiter performance dashboard
  The currency question gets asked even when every chart in the request is
  a plain count — worth skipping it until a monetary field is actually
  about to be formatted.
  → Resolved 2026-08-22: CLAUDE.md "Value formatting" now only asks when
    the confirmed chart set includes at least one monetary field.
-->
