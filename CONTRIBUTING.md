# CONTRIBUTING

## Who does what

See [docs/process/team-roles.md](docs/process/team-roles.md) and [docs/process/branching-strategy.md](docs/process/branching-strategy.md).

## Before you open a PR

```powershell
git fetch origin
git checkout develop
git pull origin develop
git checkout -b feature/BMS-n-short-name
pip install -e ".[dev]"
ruff check src tests
pytest
```

## Review

- Richard reviews calculation-heavy diffs (checkout, tax, stock).
- Stephen reviews tests and order/request flows.
- Damian reviews auth, Docker, CI, and anything that touches secrets.

Do not commit `.env`, database files, or `backups/`.
