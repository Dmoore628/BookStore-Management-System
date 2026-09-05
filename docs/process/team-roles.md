# Team roles

Course vision listed Product Owner, Scrum Master, two developers, and one tester. This example maps those hats onto **three people** without inventing extra headcount.

| Person | Product Owner | Scrum Master | Developer | Tester / QA |
| --- | --- | --- | --- | --- |
| **Damian J. Moore** | Primary | — | Auth, architecture, CI, Docker, production | Reviews Richard/Stephen PRs |
| **Richard Mora** | — | Primary | Inventory, POS, sales log | Reviews Damian/Stephen PRs; calculation checks |
| **Stephen Merten** | — | Backup facilitator | Supplier orders, customer requests, backups | Primary QA: test plan, coverage gate, UAT script |

## Why this split

A three-person store project cannot honestly run five full-time roles. Damian still owns backlog priority (PO). Richard still runs standup and the board (SM). Every story has a named developer and a named reviewer who did not write the code.

## Working agreements

- Daily standup: 15 minutes, written in `docs/process/standups/` when remote.
- Slack-style comms are replaced here by GitHub PR comments (the course listed Slack; this repo is the durable record).
- Jira is replaced by GitHub issues using `.github/ISSUE_TEMPLATE/story.md`, IDs BMS-1 … BMS-8.
