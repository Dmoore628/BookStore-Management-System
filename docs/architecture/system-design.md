# System design — Ledger & Spine

**Authors:** Damian J. Moore (architecture), Richard Hale (POS/inventory), Stephen Park (orders/QA)  
**Status:** Implemented  
**Date:** 2026-08-24

## Context

A single-store independent bookstore still runs on paper. The product is a **staff console** that behaves like desktop software: it runs on the store PC (browser at `localhost`) and talks to one database.

## Style

Layered monolith (not microservices). Three people cannot operate a distributed system honestly in two sprints.

```
Staff browser  →  FastAPI (HTML + JSON)  →  Domain services  →  SQLAlchemy  →  SQLite / PostgreSQL
```

| Layer | Responsibility | Owner |
| --- | --- | --- |
| `web/pages.py` + templates | Forms cashiers already understand | Richard / Stephen |
| `api/routers/*` | Stable JSON for tests and future register hardware | Damian |
| `services/*` | Tax, stock ledger, encryption | Split by story |
| `models/*` | Tables | Damian + Richard |
| `config.py` | Environment only — tax rate, secrets, DB URL | Damian |

## Key rules

1. **Money is `Decimal`**, never `float`.
2. **On-hand quantity changes only through `StockMovement`** (sale, receipt, opening, correction).
3. **Tax rate is `TAX_RATE_BPS` in the environment**, not a literal in checkout code.
4. **Passwords are bcrypt hashes.** Customer contact is Fernet ciphertext. Cashiers cannot decrypt contact.
5. **Roles:** cashier < manager < owner.

## Environments

| Name | Git branch | Database | Notes |
| --- | --- | --- | --- |
| development | `develop` + feature | SQLite file or Compose Postgres | Hot reload |
| test | CI / `pytest` | Temporary SQLite | Isolated per run |
| staging | `staging` | PostgreSQL | Owner demo, HTTPS cookies |
| production | `main` | PostgreSQL | Store PC or small VM |

## Security notes

Session cookie is signed with `SECRET_KEY`. Staging/production set `SESSION_HTTPS_ONLY=true` behind TLS. Encryption key is required at boot; losing it makes stored contacts unreadable (restore from backup JSON taken while the key was valid).

## Why not a native `.exe` GUI?

The course vision asked for desktop software. A local web console is still a single-machine install, is testable in CI, and matches how most modern POS terminals work. Wrapping the same URL in a WebView is a later packaging step, not a second product.
