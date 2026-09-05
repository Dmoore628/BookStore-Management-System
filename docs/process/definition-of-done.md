# Definition of Done

Taken from the CS491 vision document and expanded into checks the three of us can actually run.

The product is **Done** when all of the following are true.

## Product

- Inventory, POS/checkout, and supplier/customer orders are coded, integrated, and sharing one database.
- A cashier can look up a title, complete cash or card checkout, and see on-hand quantity drop without typing a new count.
- Tax, totals, and cash change match independent arithmetic (basis points from `TAX_RATE_BPS`).
- A manager can open the day drawer (cash vs card totals).
- Incoming supplier orders can be logged and marked received; receiving increases stock.
- Customer special-order requests can be logged; contact is encrypted; cashiers cannot read contact.
- Staff must sign in. Passwords are bcrypt hashes. No secrets in Git.

## Quality

- `pytest` is green.
- Coverage of `src/bookstore` is **at least 80%** (`--cov-fail-under=80` in `pyproject.toml` and in CI).
- Ruff reports no issues on `src` and `tests`.
- Manual walkthrough of the story’s staff-console screen is recorded on the pull request.

## Release

- User manuals exist (`docs/user/`).
- The release candidate is on `staging`, then merged to `main`.
- The owner (Damian, acting as Product Owner) signs the [release checklist](release-checklist.md).
