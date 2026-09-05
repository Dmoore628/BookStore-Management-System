# Environments and databases

| Name | Git branch | Compute | Database | Secrets |
| --- | --- | --- | --- | --- |
| Local | `feature/*` | Laptop, `uvicorn` | SQLite file `bookstore_dev.db` | `.env` (gitignored) |
| Test | CI / `pytest` | GitHub Actions | Temporary SQLite | Generated in `tests/conftest.py` |
| Development compose | `develop` | Docker | PostgreSQL 16 (`bookstore_pg` volume) | `.env` injected into Compose |
| Staging | `staging` | Docker overlay `docker-compose.staging.yml` | PostgreSQL, no host port published in overlay intent | `SESSION_HTTPS_ONLY=true` |
| Production | `main` | Docker overlay `docker-compose.prod.yml` | PostgreSQL, restart policies on | Same as staging; passwords rotated |

## Schema

Logical model: [database.md](../architecture/database.md) and [erd.md](../architecture/erd.md).

Alembic revision `0001_initial` creates tables from SQLAlchemy metadata. Application startup also calls `create_all` so a cashier laptop using SQLite can boot without a separate migrate command. Staging/production should still run:

```powershell
alembic upgrade head
```

## What is not stored in Git

`SECRET_KEY`, `ENCRYPTION_KEY`, `INITIAL_OWNER_PASSWORD`, `POSTGRES_PASSWORD`, and seed staff passwords. Losing `ENCRYPTION_KEY` makes stored customer contacts unreadable; restore from a backup taken while the key was valid.
