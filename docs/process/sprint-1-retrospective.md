# Sprint 1 retrospective

**Dates:** 2026-08-24 through 2026-09-04  
**Facilitator:** Richard Hale  
**Attendees:** Damian J. Moore, Richard Hale, Stephen Park

## Went well

- Splitting PO / SM / QA hats onto three people stopped us from pretending we had a five-person Scrum team.
- Pinning tax tests to 725 basis points caught a float rounding mistake in the first checkout sketch.
- Feature branches named after BMS IDs made the GitHub board match the Excel backlog.

## Could have gone better

- The original workbook listed a single developer. We spent the first planning meeting mapping Damian / Richard / Stephen onto every role instead of coding.
- SQLite on the laptop vs PostgreSQL in Compose needed an explicit environments doc; Stephen tripped on that during the first CI run locally.

## Surprised us

- Course vision said “desktop software.” A local browser console is what modern registers actually are. We documented that so the owner is not expecting a WinForms `.exe` in sprint 1.

## Change for sprint 2

- Stephen owns the coverage gate in CI. PRs that drop below 80% do not merge.
- Richard time-boxes standup to 15 minutes and writes a four-line note when someone is remote.
