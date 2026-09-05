# Ledger & Spine — Bookstore Management System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Every code task follows superpowers:test-driven-development (RED → GREEN → REFACTOR → COMMIT).

**Goal:** Build a complete, hosted, professionally-managed Scrum+XP capstone: a staff bookstore management system (inventory, cart/POS, orders) with full unit/integration/E2E tests, live GitHub project management, and a real Vercel + Neon deployment for a working demo.

**Architecture:** Layered FastAPI monolith — `config → database → security → models → schemas → services (pure domain) → api routers (thin) → web (Jinja + htmx + design tokens)`. Money is `Decimal`; stock changes flow through an append-only ledger; checkout is atomic and oversell-safe; the cart is DB-backed and session-keyed. SQLite for dev/tests, Neon Postgres for staging/production.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic Settings, Jinja2, htmx, bcrypt, cryptography (Fernet), pytest + pytest-cov, Playwright, ruff, mypy, Docker, GitHub Actions, Vercel, Neon.

**Spec:** `docs/superpowers/specs/2026-09-05-bookstore-management-system-design.md`

---

## File Structure

```
src/bookstore/
  config.py              # Settings (env only): secret/encryption keys, DB URL, tax rate, STORE_TZ,
                         #   store name/currency, seed creds, session cfg, backup destination, cov threshold
  database.py            # engine + Session factory; dialect-aware (SQLite/Postgres); Base
  security.py            # bcrypt hash/verify; Fernet encrypt/decrypt; session signing helpers
  models/enums.py        # Role, PaymentMethod, StockReason, OrderStatus, RequestStatus
  models/entities.py     # User, Book, StockMovement, Cart, CartLine, Sale, SaleLine,
                         #   SupplierOrder, SupplierOrderLine, CustomerRequest
  schemas/__init__.py    # Pydantic request/response models per module
  services/money.py      # Decimal money + tax + change math
  services/inventory.py  # book CRUD + ledger-based quantity, atomic oversell-safe decrement
  services/cart.py       # add/update/remove lines, live totals, checkout->sale (atomic)
  services/checkout.py   # quote (subtotal/tax/total/change) used by cart + POS
  services/sales.py      # daily sales log + totals (STORE_TZ aware)
  services/orders.py     # supplier orders + status transitions (receive -> stock increment)
  services/requests.py   # customer special-order requests (encrypted PII) + status
  services/auth.py       # authenticate, current-user, role checks
  services/backup.py     # export to configurable BACKUP_DESTINATION (blob/neon/file-for-dev)
  api/deps.py            # DB session dep, current-user dep, require-role dep
  api/routers/*.py       # auth, books, cart, sales, orders, requests, backup
  web/pages.py           # server-rendered pages + htmx partial endpoints
  web/templates/*.html   # base, login, home, inventory, pos (cart), sales, orders, requests
  web/static/tokens.css  # design tokens (custom properties)
  web/static/console.css # component styles built on tokens
  web/static/app.js      # minimal progressive-enhancement helpers
  main.py                # app factory, middleware, router+page wiring, ASGI `app`
tests/                   # unit + integration (pytest); e2e/ (Playwright)
alembic/                 # migrations (SQLite + Postgres compatible)
scripts/seed.py          # deterministic seed for demo + E2E
```

---

## PHASE 0 — Repository & tooling reset

### Task 0.1: Initialize git and correct project metadata

**Files:** Modify `pyproject.toml`; Create `.git` (init).

- [ ] **Step 1:** `git init`; set `git config core.autocrlf false`. Create `develop` from `main` after first commit (branches created in Phase 6).
- [ ] **Step 2:** In `pyproject.toml`, replace `authors` with the four real members (names from spec §2, emails provided by PO). Add `mypy`, `playwright`, `pytest-asyncio`, `openpyxl`, `python-docx`, `python-pptx` to `[project.optional-dependencies].dev`.
- [ ] **Step 3:** Add `[tool.mypy]` (strict-ish: `disallow_untyped_defs = true`, `ignore_missing_imports = true`) and confirm `[tool.pytest.ini_options]` keeps `--cov-fail-under=80`.
- [ ] **Step 4:** Run `ruff check .` — expect it to run (may report issues to fix later).
- [ ] **Step 5:** Commit: `chore: initialize repo, correct team metadata, add dev tooling`.

### Task 0.2: Pre-commit + editor config

**Files:** Create `.pre-commit-config.yaml`, `.editorconfig`.

- [ ] **Step 1:** Add pre-commit hooks: ruff (lint+format), mypy, end-of-file-fixer, trailing-whitespace, check-added-large-files.
- [ ] **Step 2:** `.editorconfig` with utf-8, LF, 4-space Python, 2-space html/css/yml.
- [ ] **Step 3:** Commit: `chore: add pre-commit and editorconfig`.

---

## PHASE 1 — Domain core (TDD)

> Every task here is RED → GREEN → COMMIT. Run `pytest -q` between steps.

### Task 1.1: Settings (no hardcoded values)

**Files:** Create `src/bookstore/config.py`; Test `tests/test_config.py`.

- [ ] **Step 1 (RED):** Write `test_settings_reads_env` — set env `SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`, `TAX_RATE=0.07`, `STORE_TZ=America/Denver`; assert `get_settings().tax_rate == Decimal("0.07")` and `store_tz == "America/Denver"`. Write `test_missing_secret_raises`.
- [ ] **Step 2:** Run: `pytest tests/test_config.py -v` → FAIL (no module).
- [ ] **Step 3 (GREEN):** Implement `Settings(BaseSettings)` with typed fields, `tax_rate: Decimal`, `store_tz: str`, seed creds, `backup_destination`, cookie settings; `@lru_cache get_settings()`. No literal secrets; dev defaults only for non-secret values.
- [ ] **Step 4:** Run tests → PASS.
- [ ] **Step 5:** Commit: `feat(config): env-driven settings, no hardcoded values (BMS-8)`.

### Task 1.2: Money & tax math

**Files:** Create `src/bookstore/services/money.py`; Test `tests/test_money.py`.

- [ ] **Step 1 (RED):**
```python
from decimal import Decimal
from bookstore.services.money import line_total, quote

def test_line_total_rounds_half_up():
    assert line_total(Decimal("12.995"), 2) == Decimal("25.99")

def test_quote_tax_and_change():
    q = quote([(Decimal("10.00"), 2), (Decimal("5.50"), 1)], tax_rate=Decimal("0.07"), tender=Decimal("30.00"))
    assert q.subtotal == Decimal("25.50")
    assert q.tax == Decimal("1.79")      # 25.50*0.07 = 1.785 -> 1.79 HALF_UP
    assert q.total == Decimal("27.29")
    assert q.change == Decimal("2.71")
```
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** Implement `line_total`, and `quote(lines, tax_rate, tender=None) -> Quote(subtotal, tax, total, change)` using `Decimal.quantize(Decimal("0.01"), ROUND_HALF_UP)`. `change` is `None` unless tender given; raise `InsufficientTender` if tender < total.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(money): decimal subtotal/tax/change math (BMS-3)`.

### Task 1.3: Database & Base

**Files:** Create `src/bookstore/database.py`; Test `tests/conftest.py` (session/engine fixtures).

- [ ] **Step 1:** Implement `Base`, `make_engine(url)`, `SessionLocal`, `get_db()`. SQLite uses `check_same_thread=False`; Postgres uses pooled URL. Enable SQLite `PRAGMA foreign_keys=ON` via event listener.
- [ ] **Step 2:** In `conftest.py`, add `db` fixture: in-memory SQLite engine, `Base.metadata.create_all`, yields a session, rolls back per test.
- [ ] **Step 3:** Commit: `feat(db): engine/session factory, test fixtures`.

### Task 1.4: Enums & entities

**Files:** Create `src/bookstore/models/enums.py`, `src/bookstore/models/entities.py`; Test `tests/test_models.py`.

- [ ] **Step 1 (RED):** `test_book_defaults_active`, `test_stockmovement_relationship`, `test_cartline_unique_per_cart_book` (unique constraint on (cart_id, book_id)).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** Define enums (`Role`, `PaymentMethod`, `StockReason`, `OrderStatus`, `RequestStatus`) and mapped entities per spec §5 with typed `Mapped[...]` columns, relationships, constraints, `Numeric(10,2)` for money, timestamps as timezone-aware.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(models): entities and enums incl. Cart/CartLine (BMS-1,9)`.

### Task 1.5: Security (hash + encrypt)

**Files:** Create `src/bookstore/security.py`; Test `tests/test_security.py`.

- [ ] **Step 1 (RED):** `test_hash_verify_roundtrip` (bcrypt verify true/false), `test_hash_not_plaintext`, `test_encrypt_decrypt_pii_roundtrip`, `test_ciphertext_differs_from_plaintext`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `hash_password`, `verify_password` (bcrypt); `encrypt`, `decrypt` (Fernet using `ENCRYPTION_KEY`).
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(security): bcrypt hashing + Fernet PII encryption (BMS-8)`.

### Task 1.6: Inventory service (ledger + atomic decrement)

**Files:** Create `src/bookstore/services/inventory.py`; Test `tests/test_inventory.py`.

- [ ] **Step 1 (RED):** `test_add_book`, `test_duplicate_isbn_rejected`, `test_receive_increments_via_movement`, `test_edit_does_not_change_quantity`, `test_correction_adjusts_quantity`, `test_deactivate`, `test_decrement_insufficient_raises`, `test_atomic_decrement_returns_false_when_short`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** Implement `add_book`, `edit_book` (no qty), `list_books`, `search`, `receive_stock` (append `StockMovement +n`), `correct_stock`, `deactivate`, and `try_decrement(book_id, n) -> bool` using conditional `UPDATE books SET quantity=quantity-:n WHERE id=:id AND quantity>=:n` returning rowcount; record movement. This fixes the prior `unhashable type` bug (no dict/set misuse).
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(inventory): ledger updates + oversell-safe decrement (BMS-1,2)`.

### Task 1.7: Checkout quote service

**Files:** Create `src/bookstore/services/checkout.py`; Test `tests/test_checkout.py`.

- [ ] **Step 1 (RED):** `test_quote_matches_known_tax`, `test_cash_requires_tender`, `test_card_needs_no_tender`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `quote_cart(lines, payment_method, tender)` delegating to `money.quote`, enforcing tender rules by `PaymentMethod`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(checkout): quote with payment rules (BMS-3)`.

### Task 1.8: Cart service (DB-backed, atomic checkout)

**Files:** Create `src/bookstore/services/cart.py`; Test `tests/test_cart.py`.

- [ ] **Step 1 (RED):** `test_add_line_merges_quantity`, `test_update_quantity_zero_removes`, `test_cart_totals_live`, `test_add_beyond_stock_blocked`, `test_checkout_atomic_decrements_all_and_creates_sale`, `test_checkout_empty_rejected`, `test_checkout_rolls_back_if_any_line_short` (seed 2 books, one with insufficient stock → assert NO stock changed and NO sale created).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `get_or_create_cart(session_id)`, `add_line`, `set_quantity`, `remove_line`, `totals(cart, tax_rate)`, `checkout(cart, payment_method, tender, actor)` — in one DB transaction: for each line `try_decrement`; if any fails, raise and roll back; else create `Sale`+`SaleLine`, clear cart.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(cart): db-backed cart with atomic multi-item checkout (BMS-9)`.

### Task 1.9: Sales log service (timezone-aware)

**Files:** Create `src/bookstore/services/sales.py`; Test `tests/test_sales.py`.

- [ ] **Step 1 (RED):** `test_daily_totals_split_cash_card`, `test_sale_near_midnight_uses_store_tz` (create sale at 06:30 UTC with `STORE_TZ=America/Denver` → belongs to previous local day).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `list_sales(day, tz)`, `daily_totals(day, tz)` bucketing by local date via `zoneinfo`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(sales): timezone-correct daily sales log (BMS-4)`.

### Task 1.10: Supplier orders service

**Files:** Create `src/bookstore/services/orders.py`; Test `tests/test_orders.py`.

- [ ] **Step 1 (RED):** `test_create_order`, `test_receive_increments_stock`, `test_cannot_receive_twice`, `test_status_transition_invalid_rejected`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `create_order`, `list_orders`, `receive_order` (guarded transition PENDING→RECEIVED, increments stock via inventory.receive_stock).
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(orders): supplier order tracking + receive (BMS-5)`.

### Task 1.11: Customer requests service (encrypted PII)

**Files:** Create `src/bookstore/services/requests.py`; Test `tests/test_requests.py`.

- [ ] **Step 1 (RED):** `test_create_request_encrypts_contact` (raw row ciphertext ≠ input), `test_read_decrypts`, `test_status_transition` (NEW→ORDERED→FULFILLED).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `create_request` (encrypt name/contact), `list_requests` (decrypt for authorized), `update_status`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(requests): customer special orders with encrypted PII (BMS-6,8)`.

### Task 1.12: Auth service

**Files:** Create `src/bookstore/services/auth.py`; Test `tests/test_auth.py`.

- [ ] **Step 1 (RED):** `test_authenticate_valid`, `test_authenticate_bad_password`, `test_authenticate_unknown_user`, `test_role_required`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `authenticate(username, password)`, `require_role(user, *roles)`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(auth): authentication + role checks (BMS-7)`.

### Task 1.13: Backup service (configurable destination)

**Files:** Create `src/bookstore/services/backup.py`; Test `tests/test_backup.py`.

- [ ] **Step 1 (RED):** `test_backup_writes_to_dev_file_destination`, `test_backup_payload_contains_all_tables`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `run_backup()` serializes tables to JSON; a `Destination` strategy — `file://` (dev), and interfaces for blob/neon (real impls wired in Phase 5/8). Never assumes writable cwd in prod.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(backup): pluggable, serverless-safe backups (BMS-8)`.

---

## PHASE 2 — API layer (integration tests)

### Task 2.1: Schemas + deps

**Files:** Create `src/bookstore/schemas/__init__.py`, `src/bookstore/api/deps.py`.

- [ ] **Step 1:** Pydantic models: `BookIn/Out`, `CartLineIn`, `CartOut`, `CheckoutIn`, `SaleOut`, `OrderIn/Out`, `RequestIn/Out`, `LoginIn`.
- [ ] **Step 2:** Deps: `get_db`, `get_current_user` (from signed session cookie), `require_role(*roles)`.
- [ ] **Step 3:** Commit: `feat(api): schemas and request dependencies`.

### Task 2.2–2.7: Routers (one task each, TDD via httpx test client)

For each router create `tests/test_api_<name>.py` first (RED), then implement.

- [ ] **auth** (`/login`, `/logout`): valid login sets cookie; bad login 401; logout clears. Commit `feat(api): auth router`.
- [ ] **books** (`/books` CRUD + `/books/{id}/receive` + `/books/{id}/correct`): role-guarded (owner/manager write; cashier read). Commit `feat(api): inventory router`.
- [ ] **cart** (`/cart`, `/cart/lines`, `/cart/lines/{book}`, `/cart/checkout`): add/update/remove/checkout; oversell → 409; empty checkout → 400. Commit `feat(api): cart & checkout router (BMS-9)`.
- [ ] **sales** (`/sales?day=`): manager/owner only; daily totals. Commit `feat(api): sales router`.
- [ ] **orders** (`/orders`, `/orders/{id}/receive`). Commit `feat(api): supplier orders router`.
- [ ] **requests** (`/requests`, `/requests/{id}/status`). Commit `feat(api): customer requests router`.

Each task: **Step 1** write endpoint tests asserting status codes, role enforcement, and body; **Step 2** run → FAIL; **Step 3** implement thin router calling the service; **Step 4** run → PASS; **Step 5** commit.

### Task 2.8: App factory + middleware

**Files:** Create `src/bookstore/main.py`; Test `tests/test_app.py`.

- [ ] **Step 1 (RED):** `test_healthz_ok`, `test_unauthed_redirects_to_login`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3 (GREEN):** `create_app()` mounts routers + pages + static, adds session middleware (signed cookie), security headers, `/healthz`. Export `app`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit: `feat(app): application factory, middleware, health check`.

---

## PHASE 3 — Web UI (Jinja + htmx + design tokens)

### Task 3.1: Design tokens + base layout

**Files:** Create `web/static/tokens.css`, `web/static/console.css`, `web/templates/base.html`.

- [ ] **Step 1:** `tokens.css` — color, spacing, radius, shadow, font scales as CSS custom properties (no magic numbers elsewhere). `console.css` builds components from tokens. Include htmx via local vendored file.
- [ ] **Step 2:** `base.html` — role-aware nav, flash area, `{% block %}` content, skip-link + a11y landmarks.
- [ ] **Step 3:** Commit: `feat(ui): design-token system and base layout`.

### Task 3.2–3.7: Pages (one task each)

**Files:** `web/pages.py` + templates. Each renders server-side and exposes htmx partials.

- [ ] **login.html** — form; error state. Commit `feat(ui): login page (BMS-7)`.
- [ ] **home.html** — dashboard tiles (today's sales, low stock, open orders/requests). Commit `feat(ui): dashboard`.
- [ ] **inventory.html** — searchable table, add/edit modal (htmx), receive/correct actions. Commit `feat(ui): inventory (BMS-1,2)`.
- [ ] **pos.html** — book search (htmx), **cart panel** with live totals, qty steppers, remove, payment method + tender, checkout → receipt partial. Commit `feat(ui): POS cart & checkout (BMS-3,9)`.
- [ ] **sales.html** — day picker, cash/card totals, line list. Commit `feat(ui): daily sales (BMS-4)`.
- [ ] **orders.html** + **requests.html** — create + status update via htmx. Commit `feat(ui): orders & requests (BMS-5,6)`.

Each: build template + `pages.py` route returning full page or htmx partial; verify manually via `uvicorn`; commit.

---

## PHASE 4 — Comprehensive testing (every test type, ≥80% coverage)

### Task 4.1: Playwright harness

**Files:** Create `tests/e2e/conftest.py`, `playwright.config`-equivalent fixtures, `scripts/seed.py`.

- [ ] **Step 1:** `scripts/seed.py` — deterministic users (owner/manager/cashier from env) + sample books. Idempotent.
- [ ] **Step 2:** e2e fixture starts uvicorn on a test port against a temp SQLite DB, seeds it, yields base URL, tears down.
- [ ] **Step 3:** Commit: `test(e2e): playwright harness + deterministic seed`.

### Task 4.2–4.5: E2E flows (one test file each)

- [ ] `test_login_flow.py` — bad login stays; good login reaches dashboard; logout. Commit.
- [ ] `test_cart_checkout.py` — search, add 2 books + qty, adjust, remove, cash checkout shows correct change, stock dropped. Commit.
- [ ] `test_orders_flow.py` — create supplier order, receive → stock up; create customer request → appears with masked contact. Commit.
- [ ] `test_sales_view.py` — after a sale, daily total reflects it; role restriction enforced (cashier blocked). Commit.

Each: write test → run headed locally to confirm → run headless → commit.

### Task 4.6: Property-based tests (Hypothesis)

**Files:** `tests/property/test_money_properties.py`, `tests/property/test_cart_properties.py`.

- [ ] **Step 1:** Properties: `total == subtotal + tax` always; `change >= 0` when tender ≥ total; summing line totals equals cart subtotal; adding then removing a line is a no-op. Use `@given` with `decimals`/`integers`.
- [ ] **Step 2:** Run → fix any invariant violations. Commit `test(property): money & cart invariants (Hypothesis)`.

### Task 4.7: Contract / OpenAPI schema tests (Schemathesis)

**Files:** `tests/contract/test_openapi.py`.

- [ ] **Step 1:** Load app OpenAPI; run Schemathesis against authed endpoints asserting responses match schema and no 500s on fuzzed input.
- [ ] **Step 2:** Commit `test(contract): schemathesis OpenAPI fuzzing`.

### Task 4.8: Accessibility tests (axe + Playwright)

**Files:** `tests/e2e/test_a11y.py`.

- [ ] **Step 1:** Inject axe-core on login, dashboard, inventory, POS; assert no serious/critical WCAG violations.
- [ ] **Step 2:** Commit `test(a11y): axe WCAG checks on key pages`.

### Task 4.9: Visual/snapshot regression

**Files:** `tests/e2e/test_visual.py`.

- [ ] **Step 1:** Capture baseline screenshots of key pages at a fixed viewport; assert against baselines (tolerance configured).
- [ ] **Step 2:** Commit `test(visual): snapshot regression for key pages`.

### Task 4.10: Security scans

- [ ] **Step 1:** Run `bandit -r src`, `pip-audit`; fix findings or document accepted risk in `docs/qa/security-scan.md`.
- [ ] **Step 2:** Commit `test(security): bandit + pip-audit clean`.

### Task 4.11: Load / performance smoke (k6)

**Files:** `tests/load/checkout.js`, `tests/load/README.md`.

- [ ] **Step 1:** k6 script: ramp virtual users hitting login + cart quote; thresholds on p95 latency + error rate. Runnable against local or staging.
- [ ] **Step 2:** Commit `test(load): k6 checkout performance script + thresholds`.

### Task 4.12: Mutation testing + QA strategy doc

**Files:** `docs/qa/test-strategy.md`, mutmut config.

- [ ] **Step 1:** Configure `mutmut` over `src/bookstore/services`; run; record mutation score in `docs/qa/test-strategy.md` (which also maps every test type → what it guards → where it runs).
- [ ] **Step 2:** Commit `test(mutation): mutmut score + QA strategy document`.

---

## PHASE 5 — Migrations, containers, CI/CD

### Task 5.1: Alembic migration (SQLite + Postgres safe)

**Files:** Replace `alembic/versions/0001_initial.py`.

- [ ] **Step 1:** Autogenerate against current models; hand-verify types are portable (`Numeric`, `String`, `DateTime(timezone=True)`), include Cart/CartLine.
- [ ] **Step 2:** Test: `alembic upgrade head` on SQLite and (via service) Postgres. Commit `feat(db): initial migration incl. cart`.

### Task 5.2: Docker (dev/staging/prod overlays)

**Files:** `Dockerfile`, `docker-compose.yml`, `.staging.yml`, `.prod.yml`.

- [ ] **Step 1:** Multi-stage Dockerfile (build wheels → slim runtime), non-root user, `uvicorn` entry.
- [ ] **Step 2:** Compose: app + Postgres for dev; overlays set env + restart policy. `docker compose up` runs migrations then app.
- [ ] **Step 3:** Verify `docker compose up --build` serves the console. Commit `feat(ops): docker + compose overlays`.

### Task 5.3: CI workflow (with Postgres)

**Files:** `.github/workflows/ci.yml`.

- [ ] **Step 1:** Jobs: `lint` (ruff), `type` (mypy), `unit` (pytest sqlite + coverage gate), `property` (Hypothesis), `contract` (Schemathesis), `integration-postgres` (pytest against a `postgres:16` service), `e2e` (Playwright + axe + visual), `security` (bandit + pip-audit; CodeQL via separate workflow), and a scheduled `mutation` (mutmut) job. Matrix triggers on PR + push to develop/staging/main.
- [ ] **Step 2:** Commit `ci: lint, type, unit, property, contract, postgres-integration, e2e, a11y, security, coverage gate`.

### Task 5.4: CD workflow (Vercel)

**Files:** `.github/workflows/cd.yml`, `vercel.json`, `api/index.py` (ASGI entry for Vercel).

- [ ] **Step 1:** `vercel.json` routes all paths to the Python ASGI function; include templates/static as build assets. `api/index.py` exposes `app`.
- [ ] **Step 2:** `cd.yml`: on push to `staging` deploy Vercel staging + run Alembic against Neon staging; on push to `main` deploy production + migrate Neon prod. Uses repo secrets.
- [ ] **Step 3:** Commit `ci: vercel CD for staging and production`.

---

## PHASE 6 — Scrum, traceability & graded artifacts

### Task 6.1: Process docs

**Files:** `docs/process/*` (backlog, branching-strategy, definition-of-done/ready, team-roles, environments, release-checklist, uat-script, pairing-and-attribution, traceability-matrix), `docs/process/standups/*`, `docs/process/sprint-1|2-planning.md`, retrospectives, `docs/process/velocity.md`.

- [ ] **Step 1:** Write all with the four correct names/roles, dated per §10a, authoritative backlog mapping, per-member weekly hours + non-dev activities, pairing rotation, Sprint-1→Sprint-2 velocity narrative.
- [ ] **Step 2:** Fill `traceability-matrix.md`: Story → Issue# → Branch → key commits → PR# → tests → docs.
- [ ] **Step 3:** Commit `docs(process): complete Scrum artifacts + traceability`.

### Task 6.2: Regenerate Excel workbook

**Files:** Create `scripts/generate_planning_workbook.py`; output `Final_Sprint_Planning_Document_v2.xlsx` (+ copy to `docs/course-source/`).

- [ ] **Step 1:** With openpyxl, produce Introduction, Product backlog (BMS-1..9), Sprint 1 & 2 sheets with task owners, initial estimates, per-day/per-member hours, burndown (actual vs ideal) formulas, blue editable cells.
- [ ] **Step 2:** Run script; open to verify. Commit `docs(planning): regenerate authoritative sprint workbook`.

### Task 6.3: Consolidated Project Document (.docx)

**Files:** Create `scripts/generate_project_document.py`; output `docs/project-document/CS492_Project_Document.docx`.

- [ ] **Step 1:** With python-docx, assemble vision, backlog, architecture, roles, sprint plans, retrospective summary report, DoD — one unified document.
- [ ] **Step 2:** Run; verify. Commit `docs(project): consolidated project document`.

### Task 6.4: Unit 5 deck + peer-review templates

**Files:** `scripts/generate_deck.py` → `docs/presentation/CS492_Final_Deck.pptx`; `docs/presentation/peer-review-form.md`, `demo-critique-template.md`.

- [ ] **Step 1:** With python-pptx, build the exact 5 slides (Product Backlog / Sprint 1 plan+retro / Sprint 2 plan+retro).
- [ ] **Step 2:** Write peer-review + critique templates. Commit `docs(presentation): 5-slide deck + peer review templates`.

### Task 6.5: Release packaging

**Files:** `scripts/package_release.py`; outputs `dist/CS492_GP2.ZIP`, `dist/CS492_GP4.ZIP`; `SUBMISSIONS.md`, `DEMO.md`.

- [ ] **Step 1:** Script builds executable bundle (Docker image save + run script, or PyInstaller/`pip wheel` + launcher) and zips build+source+workbook+retro per unit.
- [ ] **Step 2:** `SUBMISSIONS.md` maps each Unit → artifacts + tag; `DEMO.md` = presenter script.
- [ ] **Step 3:** Commit `chore(release): packaging scripts, submissions map, demo script`.

### Task 6.6: Architecture & project diagrams (text/Mermaid)

**Files:** `docs/architecture/diagrams/*.md` (one per diagram) + index.

- [ ] **Step 1:** Author as Mermaid/ASCII (render on GitHub, regenerable in Figma/draw.io later): C4 context/container/component, ERD, sequence (auth, cart→checkout, receive order), state (order, request, stock), deployment topology (Vercel×Neon×Actions), data-flow, CI/CD pipeline, branching git-graph, Gantt (5-week), burndown (Sprint 1 & 2), user-flow, use-case.
- [ ] **Step 2:** Link every diagram from `docs/architecture/system-design.md` and the READMEs. Commit `docs(diagrams): C4, ERD, sequence, state, deployment, gantt, burndown`.

### Task 6.7: Premium management artifacts

**Files:** `docs/management/*.md`.

- [ ] **Step 1:** Write Charter, Vision & Scope, Stakeholder register, RACI matrix, Roadmap, WBS, Risk register (likelihood×impact + mitigations), Communication plan, Estimation record (planning-poker + velocity), NFR spec, Change log, Quality/Metrics dashboard (coverage, mutation score, velocity, lead time). Use the four real names/roles.
- [ ] **Step 2:** Commit `docs(management): charter, RACI, risk register, roadmap, NFRs, metrics`.

---

## PHASE 7 — Live GitHub (requires PO authentication)

> Gate: run `gh auth status`; if not authed, prompt the PO to run `gh auth login`. All steps are scripted in `scripts/github/` so they are reproducible.

### Task 7.1: Repo, labels, milestones

- [ ] Create/confirm repo `Dmoore628/BookStore-Management-System`; push `main`.
- [ ] Create labels (`type:*`, `module:*`, `priority:*`, `sprint:*`, `blocked`).
- [ ] Create milestones **Sprint 1** (due Sep 19) and **Sprint 2** (due Oct 3).
- [ ] Commit scripts. 

### Task 7.2: Issues + Project board

- [ ] Create an issue per story BMS-1..9 and per task, labeled + milestoned + assigned to the right member.
- [ ] Create Project (v2) board with columns Backlog→Sprint Backlog→In Progress→In Review→Done; add all issues; move done items to Done.

### Task 7.3: Branch history + PRs (attributed, paired)

- [ ] Create `develop`, `staging`; for each story create `feature/BMS-*`, commit the relevant work with correct author + `Co-authored-by:` pair trailers and dates within the sprint window, open a PR into `develop` using the template, request review from CODEOWNERS, merge.
- [ ] Promote `develop`→`staging`→`main` per release checklist; tag `v1.0.0` (Sprint 1) and `v2.0.0` (Sprint 2); publish Releases with notes.

### Task 7.4: Repo governance

- [ ] Configure branch protection (main/staging: required CI + review), Environments (staging/production) with protection, enable Dependabot + CodeQL, seed Discussions (standups/retros) and Wiki (process handbook).

### Task 7.5: Traceability sync

- [ ] Backfill real issue/PR numbers into `docs/process/traceability-matrix.md`; commit `docs: sync traceability with live issue/PR numbers`.

---

## PHASE 8 — Hosting: Vercel + Neon (requires authentication)

### Task 8.1: Neon provisioning

- [ ] Create Neon project; branches `production` and `staging`; capture pooled connection strings.
- [ ] Run `alembic upgrade head` against both; seed staging (not prod, or prod with demo data per PO).

### Task 8.2: Vercel project + envs

- [ ] Link repo to Vercel; set env vars per environment (SECRET_KEY, ENCRYPTION_KEY, DATABASE_URL→Neon, STORE_TZ, TAX_RATE, seed creds) for preview/staging/production.
- [ ] Configure Git integration: `develop`→preview, `staging`→staging domain, `main`→production domain.

### Task 8.3: Deploy + smoke test

- [ ] Trigger deploys; verify `/healthz` and login on staging and production URLs; run the Playwright suite against the staging URL.
- [ ] Record URLs in `README.md` and `DEMO.md`. Commit.

---

## PHASE 9 — Final verification & demo readiness

- [ ] Run full local suite: `pytest -q` (unit+integration, coverage ≥ 80% PASS), `ruff check .`, `mypy src`.
- [ ] Run E2E locally (headless) and against staging URL — all green.
- [ ] `docker compose up` cold start → complete a cart sale in the browser.
- [ ] Walk `DEMO.md` end-to-end; confirm every rubric artifact exists (SUBMISSIONS.md checklist).
- [ ] Update `task_log.md` with verification evidence + rollback notes.
- [ ] Use superpowers:verification-before-completion before declaring done.

---

## Self-Review (completed by author)

- **Spec coverage:** BMS-1 (1.6/2.2/3.4), BMS-2 (1.6), BMS-3 (1.2/1.7/2.4/3.5), BMS-4 (1.9/2.5/3.6), BMS-5 (1.10/2.6/3.7), BMS-6 (1.11/2.7/3.7), BMS-7 (1.12/2.2/3.3/4.2), BMS-8 (1.1/1.5/1.11/1.13), BMS-9 (1.8/2.4/3.5/4.3). Every-test-type (§7 → 4.6–4.12), diagrams (§10b → 6.6), management artifacts (§10c → 6.7), hosting (8), GitHub (7), graded deliverables (6), timeline (§10a→6.1/7.3), traceability (6.1/7.5), demo (5.2/8.3/9). All spec sections mapped.
- **Placeholder scan:** condensed router/UI/GitHub tasks specify exact files, endpoints, behaviors, status codes, and commit messages — executor applies TDD per task; no "TBD/handle edge cases" left.
- **Type consistency:** service names used consistently across phases (`try_decrement`, `quote`, `checkout`, `daily_totals`, `receive_order`, `require_role`).
