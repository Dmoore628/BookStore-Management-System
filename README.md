# Ledger & Spine — Bookstore Management System

Staff software that replaces paper stock cards, the cash-register log, and the special-order notebook for a small independent bookstore.

GitHub: [Dmoore628/BookStore-Management-System](https://github.com/Dmoore628/BookStore-Management-System)

## What this means for the store

Cashiers look up a title, take cash or card, and the shelf count drops by itself. Managers see today’s drawer, mark a publisher shipment received, and take special orders without leaving a sticky note on the counter. Passwords are never stored in readable form. Customer phone numbers and emails are encrypted.

## Team

| Name | Roles on this project |
| --- | --- |
| **Damian J. Moore** | Product Owner, solution architecture, authentication and secrets, CI/CD, production branch |
| **Richard Mora** | Scrum Master, inventory module, POS/checkout math, daily sales log |
| **Stephen ** | QA lead, supplier orders, customer requests, backups, automated tests |

## Branches (how the GitHub repo is organized)

| Branch | Purpose |
| --- | --- |
| `main` | Production. Only merged from `staging` after a release checklist. |
| `staging` | Pre-production. Merged from `develop` for owner demo and staff UAT. |
| `develop` | Integration. Feature branches merge here after review. |
| `feature/BMS-*` | One branch per backlog item (see `docs/process/branching-strategy.md`). |

## Run locally (without Docker)

1. Copy `.env.example` to `.env` and fill in `SECRET_KEY`, `ENCRYPTION_KEY`, and `INITIAL_OWNER_PASSWORD`.
2. Create a virtual environment and install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m scripts.seed
uvicorn bookstore.main:app --reload --host 127.0.0.1 --port 8000
```

3. Open http://127.0.0.1:8000 and sign in.

| Seed user | Role |
| --- | --- |
| `INITIAL_OWNER_USERNAME` (example: `damian`) | owner |
| `richard` | manager |
| `stephen` | cashier |

Passwords come from `.env` (`INITIAL_OWNER_PASSWORD`, `SEED_MANAGER_PASSWORD`, `SEED_CASHIER_PASSWORD`). Never commit the real `.env`.

Generate a Fernet key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Tests

```powershell
pytest
```

CI fails the build if coverage of `src/bookstore` is under **80%**.

## Docker

Docker Desktop is used for PostgreSQL-backed staging/production-like runs.

```powershell
copy .env.example .env
docker compose up --build
```

Staging / production overlays:

```powershell
docker compose -f docker-compose.yml -f docker-compose.staging.yml up --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

## Documentation map

| Document | Audience |
| --- | --- |
| `docs/user/staff-manual.md` | Cashiers and managers (non-technical) |
| `docs/user/business-guide.md` | Bookstore owner |
| `docs/architecture/system-design.md` | Developers |
| `docs/architecture/database.md` | Developers / DB |
| `docs/process/branching-strategy.md` | Whole team |
| `docs/process/definition-of-done.md` | Whole team |
| `docs/process/team-roles.md` | Whole team |
| `task_log.md` | Build diary |

## Rollback

- **Application:** redeploy the previous `main` image/tag; database stays compatible within a release.
- **Feature flag equivalent:** deactivate a book rather than deleting sales history.
- **Data:** restore the latest JSON file from `BACKUP_DIR` (manager action in the console).

## License

Course example project. Course source artifacts are stored in `docs/course-source/`.
