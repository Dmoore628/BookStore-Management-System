<div align="center">

# 📚 Ledger & Spine — Bookstore Management System

**A staff-facing system that replaces a small bookstore's paper stock cards, cash-register log, and special-order notebook with one reliable application.**

CS492 Capstone · Colorado Technical University · Group 6
Scrum + XP · FastAPI · PostgreSQL · Vercel

[Repository](https://github.com/Dmoore628/BookStore-Management-System) ·
[Architecture](docs/architecture/system-design.md) ·
[Process & Scrum](docs/process/) ·
[Design spec](docs/superpowers/specs/2026-09-05-bookstore-management-system-design.md)

</div>

---

## What it does

| Module | Story | What the staff can do |
|---|---|---|
| **Inventory** | BMS-1, BMS-2 | Add/edit/search books; stock updates automatically through an append-only ledger |
| **Cart & POS** | BMS-3, BMS-9 | Build a multi-item cart, see live tax/totals, take cash or card, get exact change |
| **Sales log** | BMS-4 | Review the day's cash vs. card takings (store-timezone correct) |
| **Supplier orders** | BMS-5 | Track incoming shipments; receiving increments stock |
| **Customer requests** | BMS-6 | Log special orders with encrypted customer contact details |
| **Access & security** | BMS-7, BMS-8 | Role-based logins; hashed passwords; encrypted PII |

## Team & Scrum roles

| Member | Scrum role | Focus |
|---|---|---|
| **Damian J. Moore** | Product Owner | Architecture, auth/secrets, CI/CD, releases |
| **Richard Mora** | Scrum Master | Inventory, POS/checkout, facilitation |
| **Stephen Merten** | Developer (QA Lead) | Testing, orders, backups, E2E |
| **Daniel Richards** | Developer | Cart, sales log, requests, UI/UX |

## Quick start (5 minutes)

```powershell
# 1. Configure — copy the template and fill in the secrets it documents
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"                    # -> SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # -> ENCRYPTION_KEY

# 2. Install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# 3. Run the tests (should be all green)
pytest

# 4. Seed demo data and launch the console
python -m scripts.seed
uvicorn bookstore.main:app --reload
```

Then open <http://127.0.0.1:8000> and sign in with the seeded accounts (see `.env`).

### With Docker (PostgreSQL-backed, closest to production)

```powershell
copy .env.example .env
docker compose up --build
```

## Architecture at a glance

A layered monolith — pure domain logic, thin HTTP layer, server-rendered UI:

```
config → database → security → models → schemas → services (domain) → api routers → web (UI)
```

- **Money** is `Decimal` end-to-end with half-up rounding — never floats.
- **Stock** is an append-only ledger; checkout uses an **atomic, oversell-safe** decrement.
- **Everything is configuration** — no hardcoded secrets or business constants (see `.env.example`).

Full detail: [`docs/architecture/system-design.md`](docs/architecture/system-design.md) ·
Repository layout: [`docs/architecture/repository-structure.md`](docs/architecture/repository-structure.md)

## Testing

```powershell
pytest                       # unit + integration, coverage gate 80%
ruff check src tests         # lint
mypy src                     # types
```

The full pyramid (property-based, contract, E2E/Playwright, accessibility, visual, security, load,
mutation) is described in [`docs/qa/test-strategy.md`](docs/qa/test-strategy.md).

## Branching & environments

`feature/BMS-*` → `develop` (integration) → `staging` (QA/UAT) → `main` (production).
See [`docs/process/branching-strategy.md`](docs/process/branching-strategy.md) and
[`docs/process/environments.md`](docs/process/environments.md).

## Documentation map

| Area | Location |
|---|---|
| Architecture, ADRs, diagrams | [`docs/architecture/`](docs/architecture/) |
| Scrum process, sprints, retros, traceability | [`docs/process/`](docs/process/) |
| Project management (charter, RACI, risk, NFRs) | [`docs/management/`](docs/management/) |
| QA & test strategy | [`docs/qa/`](docs/qa/) |
| User guides | [`docs/user/`](docs/user/) |
| Original course source | [`docs/course-source/`](docs/course-source/) |
| Design spec & implementation plan | [`docs/superpowers/`](docs/superpowers/) |

## License

MIT — see [LICENSE](LICENSE). Course source artifacts are preserved in `docs/course-source/`.
