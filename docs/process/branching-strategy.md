# Branching strategy

**Owners:** Damian J. Moore (DevOps), Richard Mora (Scrum Master)

This repository uses a three-lane Gitflow. Feature work never lands directly on production.

```
feature/BMS-*  →  develop  →  staging  →  main
```

| Branch | Environment | Who merges | Rule |
| --- | --- | --- | --- |
| `feature/<id>-<slug>` | Developer laptop | Author, via PR | One backlog item. Branched from latest `develop`. |
| `develop` | Integration | Reviewer (not the sole author when possible) | CI green. Coverage ≥ 80%. |
| `staging` | PostgreSQL staging stack | Damian after PO demo | Same commit as the release candidate. |
| `main` | Production | Damian after the [release checklist](release-checklist.md) | Fast-forward or merge commit from `staging` only. |

## Feature branch names (this product)

| Branch | Story | Primary author |
| --- | --- | --- |
| `feature/infra-bootstrap` | Repo, Docker, models, Alembic | Damian |
| `feature/BMS-7-authentication` | Logins and roles | Damian |
| `feature/BMS-1-inventory` | Stock cards | Richard |
| `feature/BMS-2-stock-movements` | Automatic quantity ledger | Richard |
| `feature/BMS-3-checkout` | Totals, tax, change | Richard |
| `feature/BMS-4-sales-log` | Daily cash/card log | Richard |
| `feature/BMS-5-supplier-orders` | Incoming POs | Stephen |
| `feature/BMS-6-customer-requests` | Special orders | Stephen |
| `feature/BMS-8-data-protection` | Encryption, backups, role gates | Damian / Stephen |
| `feature/ci-docs` | CI, manuals, Definition of Done | Stephen / Damian |

## Pull requests

1. Open the PR against `develop` using `.github/PULL_REQUEST_TEMPLATE.md`.
2. CI (`.github/workflows/ci.yml`) must pass Ruff and pytest.
3. Stephen records a test note on stories he did not write; Damian or Richard records one on stories Stephen wrote.
4. Merge with a merge commit (not squash) so GitHub still shows the feature branch name in history.
5. Delete the feature branch after merge.

## Simulated remote collaboration

Each developer pulls `develop` before branching:

```powershell
git fetch origin
git checkout develop
git pull origin develop
git checkout -b feature/BMS-n-short-name
```

After review:

```powershell
git checkout develop
git pull origin develop
git merge --no-ff feature/BMS-n-short-name
git push origin develop
```

Release:

```powershell
git checkout staging
git pull origin staging
git merge --no-ff develop
git push origin staging
# after UAT
git checkout main
git merge --no-ff staging
git push origin main
```
