# Design Spec — "Ledger & Spine" Bookstore Management System

**Course:** CS492 (Colorado Technical University), Group 6 — Capstone execution & delivery
**Date:** 2026-09-05
**Author of record:** Damian J. Moore (Product Owner)
**Status:** Approved for planning

---

## 1. Purpose & success criteria

Replace a small independent bookstore's paper stock cards, cash-register log, and special-order
notebook with one reliable, staff-facing software system, delivered as a professional Scrum+XP
capstone with full GitHub project management, a real hosted environment, and a working live demo.

**Success (plain English):**
- A cashier can search books, build a **cart**, sell it, and stock drops immediately.
- Totals, tax, and cash change match a calculator, to the cent.
- A manager/owner can see today's cash vs. card sales.
- Supplier orders and customer special-order requests are tracked.
- Only authenticated staff can use the system; passwords are hashed; customer PII is encrypted at rest.
- Automated tests (unit + integration + **end-to-end**) cover ≥ 80% of application code and pass in CI.
- The app is **hosted on a real URL with a real managed Postgres database** for the demo.
- Every requirement is **traceable**: Story → Issue → Branch → Commits (with pair authors) → PR → Tests → Docs.

**Explicit non-goals (YAGNI):** e-commerce/customer-facing storefront, payment-gateway integration,
multi-store tenancy, barcode hardware, accounting exports. These are out of scope.

## 2. Team & Scrum roles (authoritative — correct everywhere)

| Person | Scrum role | Engineering focus |
|---|---|---|
| **Damian J. Moore** | Product Owner | Architecture, auth/secrets, CI/CD, production releases |
| **Richard Mora** | Scrum Master | Inventory module, POS/checkout math, facilitation |
| **Stephen Merten** | Developer (QA Lead) | Test strategy, supplier/customer orders, backups, E2E |
| **Daniel Richards** | Developer | Cart, daily sales log, customer requests, UI/UX, integration |

Older files used incorrect surnames (e.g. "Richard Hale", "Stephen Park") and a single placeholder
owner. These have been corrected in every source, doc, and metadata file.

**Attribution:** git authorship, pair-programming `Co-authored-by:` trailers, and PR authorship use
each member's real name + GitHub email (provided by the PO). History is reconstructed by the tooling
but authentically attributed; `docs/process/pairing-and-attribution.md` states this transparently.

## 3. Methodology — Scrum + XP

Scrum is the framework (matches the CS492 rubric): Product Owner, Scrum Master, Development Team;
two 2-week sprints; sprint planning, daily standups, sprint review/demo, retrospective; product &
sprint backlogs; burndown & velocity. XP engineering practices are layered in and evidenced:
**pair programming** (co-authored commits + documented pairing sessions), **test-driven development**,
**continuous integration**, and **small, frequent releases**.

## 4. Product scope — modules & backlog

Three modules on one database, plus cross-cutting auth/security.

| Story | Title | Sprint | Module |
|---|---|---|---|
| BMS-1 | Manage Book Inventory Records | 1 | Inventory |
| BMS-2 | Automatic Stock Quantity Updates | 1 | Inventory |
| BMS-3 | Checkout Calculation (Totals, Tax, Change) | 1 | POS |
| BMS-7 | User Login and Access Control | 1 | Auth |
| **BMS-9** | **Shopping Cart / Multi-item Checkout** *(new)* | 1 | POS |
| BMS-4 | Daily Cash/Card Sales Log | 2 | POS |
| BMS-5 | Supplier Order Tracking | 2 | Orders |
| BMS-6 | Customer Special Order Requests | 2 | Orders |
| BMS-8 | Protect Sales and Customer Data | 2 | Security |

**BMS-9 (cart) acceptance criteria:** A cashier can add multiple distinct books (each with a
quantity) to a cart; the cart shows live per-line and total subtotal/tax/total; quantities can be
changed and lines removed; over-selling beyond stock is blocked with a clear message; checkout
commits the entire cart as **one atomic transaction** — every line decrements stock (via an atomic,
oversell-safe conditional update), one sale record is written with its line items, tender/change is
computed for cash. Empty-cart checkout is rejected. The cart is **persisted in the database**
(`Cart`/`CartLine`, keyed by the signed session id) so it survives across stateless serverless
requests, and is cleared/converted on successful checkout.

**Note — source mapping correction:** the stale Excel maps some tasks to the wrong story (e.g. a
"build login screen" task under BMS-2, and BMS-7 in Sprint 2). This spec defines the authoritative
mapping in the table above; the correction is documented in `docs/process/backlog.md`.

## 5. Architecture

Layered monolith (as recorded in ADR-0001), packaged for both a one-command local demo and
serverless hosting.

```
src/bookstore/
  config.py          # Pydantic settings — ALL config from env, no hardcoded values
  database.py        # engine/session; SQLite (dev/test) & Postgres (staging/prod)
  security.py        # bcrypt password hashing, Fernet PII encryption, signed sessions
  models/            # SQLAlchemy entities + enums
  schemas/           # Pydantic request/response models
  services/          # domain logic (money, inventory, cart, checkout, sales, orders,
                     #   requests, auth, backup) — pure, unit-tested, no HTTP knowledge
  api/routers/       # thin FastAPI routers -> call services
  web/               # Jinja templates + design-token CSS + htmx; server-rendered console
  main.py            # app factory, middleware, router wiring, ASGI entrypoint
```

**Design rules:** each service has one clear purpose and a typed interface; routers are thin;
money is `Decimal` end-to-end (ADR-0002); inventory changes go through a **stock ledger** of
movements rather than in-place edits (ADR-0003), giving a full audit trail and safe corrections.
Stock decrements at checkout use an **atomic oversell-safe update** (conditional `UPDATE ... WHERE
quantity >= n` / `SELECT ... FOR UPDATE`) so concurrent cashiers cannot oversell the last copy.
All time-of-day logic (e.g. "today's sales") uses a **configurable store timezone** (`STORE_TZ`),
not the server's UTC clock.

**Data model (core):** `User` (role enum, password_hash), `Book` (title, author, isbn, price,
quantity, shelf_location, active), `StockMovement` (book, delta, reason, actor, ts), `Cart` +
`CartLine` (session id, book, quantity — the working basket), `Sale` + `SaleLine` (payment method,
subtotal, tax, total, tender, change), `SupplierOrder` + line items (status enum), `CustomerRequest`
(encrypted name/contact, status enum). The DB-backed cart materializes into `Sale`+`SaleLine` on
checkout and is then cleared.

**Configuration (no hardcoded values):** secret key, encryption key, database URL, tax rate,
store name/currency, **store timezone (`STORE_TZ`)**, seed usernames & passwords, session cookie
settings, backup destination, coverage threshold — all sourced from environment / settings with
documented dev-only defaults.

## 6. UI / UX

Server-rendered Jinja pages enhanced with **htmx** for partial updates (cart, search, status
changes) and a cohesive **design-token CSS system** (colors, spacing, typography as CSS custom
properties — no magic numbers). Pages: Login, Home/Dashboard, Inventory, POS+Cart, Sales, Supplier
Orders, Customer Requests. Role-aware navigation. Accessible (labels, focus states, keyboard). Goal:
an intuitive, professional "staff console" that demos impressively without a heavy JS build chain.

## 7. Testing strategy ("every single test")

- **Unit:** money/tax/change math, inventory ledger, cart totals & quantity rules, checkout
  atomicity, order/request state machines, security (hashing/encryption).
- **Integration:** FastAPI routers via httpx test client — auth flows, role enforcement, each
  module's endpoints, cart→checkout end-to-end at the API layer.
- **End-to-end (Playwright):** real browser against the running app — login, add books to cart,
  adjust quantities, checkout (cash + card), receive a supplier order, file a customer request,
  view daily sales. Doubles as the automated demo.
- **Gate:** `--cov-fail-under=80` on `src/bookstore`; ruff + mypy clean. All run in CI on every PR.
- **Dialect parity:** unit tests run on SQLite for speed, but CI **also runs the integration suite
  against a real PostgreSQL service container** so QA mirrors production and dialect bugs (Numeric,
  constraints, locking) are caught before staging.

**Every test type (industry-grade test pyramid):** beyond unit / integration / E2E, the suite adds
**property-based** (Hypothesis — money/tax invariants, cart quantity laws), **contract/API-schema**
(Schemathesis fuzzing the OpenAPI spec), **mutation testing** (`mutmut` — proves tests actually
catch regressions), **security** (`bandit` SAST, `pip-audit`/Dependabot for deps, CodeQL, secret
scanning), **accessibility** (axe via Playwright — WCAG checks), **visual/snapshot regression**
(Playwright screenshots), **smoke** (post-deploy health), **load/performance** (k6 or Locust against
staging), and **regression** (bugs get a failing test first). Coverage gate stays **≥ 80%** with
`term-missing`; mutation score is reported. A `docs/qa/test-strategy.md` maps each type to what it
guards and where it runs.

## 8. Branching, environments & CI/CD

`feature/BMS-*` → `develop` (integration) → `staging` (QA/UAT) → `main` (production).

| Env | Branch | Where | Database |
|---|---|---|---|
| Development | feature/* & develop | local + Vercel preview | SQLite / Neon dev branch |
| QA / Staging | staging | Vercel (staging) | Neon (staging) |
| Production | main | Vercel (production) | Neon (production) |

**Hosting:** FastAPI on **Vercel** Python runtime; **Neon** serverless Postgres as the real managed
database (a Neon branch per environment). Alembic migrations run as a deploy/CI step against the
target Neon branch (never at request time). Sessions are signed cookies (stateless — serverless-safe);
the cart persists in Postgres, not memory. Connection uses Neon's **pooled** URL.

**Secrets per environment:** `SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`, `STORE_TZ`, tax rate,
and seed credentials are set as **Vercel environment variables scoped to preview / staging /
production** and as GitHub Actions secrets — never committed. `.env.example` documents every key.

**Backups (serverless-safe):** because Vercel's filesystem is ephemeral/read-only, the backup
service targets durable storage — a Neon SQL export or Vercel Blob — instead of local disk; the
destination is configurable via `BACKUP_DESTINATION`.

**GitHub Actions:** `ci.yml` (lint → type-check → unit → integration → E2E → coverage gate) on every
PR and push; `cd.yml` deploys `staging`→staging and `main`→production via Vercel. Branch protection
on `main`/`staging` requires green CI + review (documented; some settings applied via API/manual).

## 9. GitHub project-management surface (full toolbox)

- **Issues** for every story (BMS-1..9) and task, with labels: `type:*`, `module:*`, `priority:*`,
  `sprint:*`, plus `good first issue`/`blocked` as needed.
- **Milestones** = Sprint 1 and Sprint 2 (with dates).
- **Project (v2)** board: Backlog → Sprint Backlog → In Progress → In Review → Done.
- **Pull Requests** per story/task, using the PR template, with reviews, **CODEOWNERS**, and
  linked issues (`Closes #`).
- **Releases/tags**: `v1.0.0` (end of Sprint 1), `v2.0.0` (end of Sprint 2).
- **Co-authored commits** (`Co-authored-by:`) documenting pair-programming pairs among the four.
- Issue/PR templates, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`.
- **Environments** (staging & production) with protection rules; **branch protection** on
  `main`/`staging` (required CI + review). **Dependabot** + **CodeQL** code scanning for security.
- **GitHub Discussions** for standups/retrospectives and **Wiki** for the process handbook, so the
  full planning/PM surface is demonstrated. `Insights` (contributors, velocity) is populated
  naturally by the attributed commit history.

## 10. Scrum & traceability artifacts (real, dated)

Under `docs/process/`: product backlog, Sprint 1 & 2 planning (with **per-member task owners +
logged hours per week, including non-development activities**), daily standup logs (with pairing
notes), sprint review/demo notes, retrospectives (Start/Stop/Continue + lessons learned), burndown &
velocity, environments, branching strategy, definition of done/ready, team roles, UAT script,
release checklist, and a **traceability matrix** (`docs/process/traceability-matrix.md`). The Excel
workbook `Final_Sprint_Planning_Document_v2.xlsx` is regenerated authoritatively (4 members, owners,
per-week hours, cart story, burndown formulas).

**Velocity-driven planning:** Sprint 1 actuals feed a documented velocity figure; Sprint 2 planning
explicitly references it to justify its committed scope (Unit 3 rubric).

**Graded deliverables produced (not just process docs):**
- **Consolidated Project Document** (`docs/project-document/`) merging the CS491 artifacts into one
  source of truth, including the **Retrospective Summary Report** — exported to `.docx`.
- **Executable build + release ZIPs**: a reproducible packaged build (Docker image + a run script /
  standalone bundle) assembled into `CS492_GP2.ZIP` (Sprint 1) and `CS492_GP4.ZIP` (Sprint 2), each
  containing the executable build, full source, updated planning workbook, and retrospective.
- **Unit 5 pack**: the **5-slide deck** (Product Backlog / Sprint 1 plan+retro / Sprint 2 plan+retro),
  plus **peer-review form templates** and a **1-page demo-critique template**.

## 10a. Timeline & weekly submission mapping

Both sprints are **built completely now**, but every dated artifact and the git/PR history are
organized so the team can **submit each week's progress on schedule** per the CS492 roadmap
(`project_context.txt`). Sprints are 2 weeks (10 working days); Sprint 1 starts **2026-09-06**.

| Unit | Week | Dates | Deliverables (submitted that week) |
|---|---|---|---|
| Unit 1 | Sprint 1 · Wk 1 | Sep 6–12 | Consolidated Project Document, Sprint 1 plan + Wk1 hours |
| Unit 2 | Sprint 1 · Wk 2 | Sep 13–19 | `CS492_GP2.ZIP` (build+source+plan+retro), Sprint 1 retro |
| Unit 3 | Sprint 2 · Wk 1 | Sep 20–26 | Refined Sprint 2 plan (velocity-based) + Wk1 hours + non-dev |
| Unit 4 | Sprint 2 · Wk 2 | Sep 27–Oct 3 | `CS492_GP4.ZIP` (final build+source+plan+retro), Sprint 2 retro |
| Unit 5 | Demo week | Oct 4–10 | 5-slide deck, live demo, peer critique + review forms |

Standups, commits, PRs, and releases carry dates within these windows so the planning docs and the
git history agree. Releases: `v1.0.0` at end of Sprint 1, `v2.0.0` at end of Sprint 2. `SUBMISSIONS.md`
maps each unit to its exact artifacts and the tag/commit that represents it.

## 10b. Diagrams (authored as text/Mermaid now; render-ready for design tools later)

All committed as Mermaid/ASCII in `docs/architecture/diagrams/` (and referenced from docs) so they
render on GitHub today and can be regenerated in Figma/draw.io later. Set:
- **C4 model** — System Context, Container, and Component diagrams.
- **ERD** — full entity-relationship diagram (all tables, keys, cardinality).
- **Sequence diagrams** — login/auth, add-to-cart → atomic checkout, receive supplier order.
- **State diagrams** — supplier order status, customer request status, stock movement lifecycle.
- **Deployment/topology** — Vercel (preview/staging/prod) ↔ Neon branches ↔ GitHub Actions.
- **Data-flow diagram** — request → router → service → ledger/DB.
- **CI/CD pipeline diagram** — PR → lint/type/test/e2e → deploy staging → deploy prod.
- **Branching (git-graph)** — feature → develop → staging → main with tags.
- **Gantt** — 5-week / 2-sprint schedule. **Burndown** charts — Sprint 1 & 2.
- **User-flow** — cashier sale journey; **use-case** diagram — roles × features.

## 10c. Planning & management artifacts (premium, industry-standard)

Under `docs/management/`, professional PM documents a Fortune-500 team would ship:
Project **Charter**, **Vision & Scope**, **Stakeholder register**, **RACI matrix**, **Roadmap**,
**Work-Breakdown Structure (WBS)**, **Risk register** (likelihood×impact + mitigations),
**Communication plan** (standup/review/retro cadence + channels), **Estimation record** (story
points / planning-poker rationale + velocity), **Non-Functional Requirements** (performance,
security, availability, scalability, accessibility, maintainability), **Definition of Ready/Done**,
**Change log**, and a **Quality/Metrics dashboard** (coverage, mutation score, velocity, lead time).
These make the repository read as a premium engineering artifact end-to-end.

## 11. The working demo

`docker compose up` (or a PowerShell/`make` script) runs the app + Postgres locally with seeded data;
the hosted Vercel URL provides the real remote demo. `DEMO.md` gives the presenter a step-by-step
script; the Playwright E2E suite runs the same flow automatically.

## 12. Known alignment note

The repo's `Final_Sprint_Planning_Document_v2.xlsx` (2026-09-02) is outdated (no cart, placeholder
roles, no owners/hours). It will be regenerated authoritatively; the user may later reconcile with
their own newer copy.

## 13. Risks & mitigations

- **FastAPI on serverless (cold starts, connection limits):** use Neon pooled connections, stateless
  signed-cookie sessions, migrations out-of-band. Fallback: Render container if Vercel proves unfit.
- **Live-auth GitHub/Vercel/Neon dependencies:** all destructive/remote steps gated on user auth;
  everything reproducible via committed scripts so the build never blocks on credentials.
- **Scope creep:** backlog frozen at BMS-1..9; non-goals in §1 enforced.
