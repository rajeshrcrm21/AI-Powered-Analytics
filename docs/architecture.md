# Architecture

## Shape

```
USER
  |
  v
Claude (this conversation, in VS Code)
  |
  v
Ask account number  ->  Ask recommendation count
  |
  v
mb auth list / status        (verify Metabase CLI config)
  |
  v
mb database / table / field  (discover the account's actual data)
  |
  v
mb query                     (analyze real data — funnels, trends, cohorts)
  |
  v
Claude ranks & explains insights
  |
  v
mb search                    (check for existing/duplicate charts)
  |
  v
mb card create / get         (create + verify confirmed charts)
  |
  v
Results returned to the user, in the terminal
```

## What does not exist here

- No web server, no REST API, no frontend, no dashboard app.
- No database is created or connected to directly by this project.
- No browser automation.
- The only "runtime" is this conversation plus the `mb` CLI subprocess calls
  Claude makes on the user's behalf.

## Why Metabase CLI, not direct DB access

The customer's actual warehouse/schema shape is unknown and instance-specific
(different accounts may be laid out differently). Metabase already models
the databases, tables, relationships, and permissions; the CLI is the
supported, auditable way to read and write through that layer without
duplicating credentials or bypassing Metabase's access model. See CLAUDE.md
for the full list of hard constraints this implies.

## Files

- `CLAUDE.md` — persistent operating instructions (read first, every time)
- `prompts/` — the four workflow stages (discovery, analysis, recommendation,
  chart-generation), referenced from CLAUDE.md
- `config/analysis-config.md` — tunable defaults/weights
- `docs/workflow.md` — the same flow, written for a human teammate
- `scripts/mb-login.sh` — thin helper that reads `.env` and calls
  `mb auth login`; everything else goes through `mb` directly, no other
  scripts are needed
