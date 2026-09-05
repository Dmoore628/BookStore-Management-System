# Task Log — Bookstore Management System

Working file for planning, progress, verification, and rollback notes.
Course source: CS491/CS492 Group 6, Colorado Technical University.

## Validation (2026-09-04)

**Business objective:** Replace paper stock cards, cash-register logs, and order notebooks with one staff-facing system that tracks inventory, checkout, supplier receipts, and customer special orders.

**Success in plain English:**
- A cashier can look up a book, sell it, and see stock drop immediately.
- Totals, tax, and cash change match what a calculator would produce.
- A manager can see today’s cash vs card sales.
- Incoming supplier orders and customer “please order this book” requests are tracked.
- Only logged-in staff can use the system; passwords are hashed; customer contact details are encrypted at rest.
- Automated tests cover at least 80% of the application code and pass.

**Prerequisites met:** Course vision/backlog documents are present under `docs/course-source/`. GitHub remote: `https://github.com/Dmoore628/BookStore-Management-System`.

**Team:** Damian J. Moore (PO, architecture, auth, DevOps), Richard Mora (SM, inventory, POS, sales), Stephen Merten (QA, orders, requests, backups).

**Branches:** `main`, `staging`, `develop`, plus one feature branch per backlog item.

---

## Entry — Implementation complete

### Subtask: Core platform

- [x] Settings from environment (no secrets in source)
- [x] Database models and migrations
- [x] Domain services and tests
- [x] HTTP API + staff UI
- [x] Docker Compose (dev / staging / prod-like)
- [x] CI workflow with coverage gate
- [x] Coverage ≥ 80%
- [x] Git feature-branch history with three authors

### Verification

Run `pytest` (fails if coverage of `src/bookstore` is under 80%) and `ruff check src tests`.

### Rollback

Redeploy previous `main`. Restore backup JSON from `BACKUP_DIR` if data is the problem.
