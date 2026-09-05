# Database design

PostgreSQL in staging/production. SQLite in automated tests and laptop development.

## Entity relationship (logical)

- **users** — staff logins (`password_hash`, role, active flag)
- **books** — title, author, ISBN (unique), price, quantity, shelf_location
- **stock_movements** — append-only quantity deltas with reason and optional sale/PO reference
- **sales** / **sale_lines** — ticket header (tender, tax, totals) and line snapshots of title/price
- **suppliers** / **supplier_orders** / **supplier_order_lines** — incoming stock
- **customer_requests** — name + encrypted contact + title requested + status
- **backup_records** — path and size of JSON snapshots

## Quantity integrity

`books.quantity` is a cached on-hand figure. Every change inserts `stock_movements` (`initial`, `sale`, `receipt`, `correction`). Sales cannot drive quantity below zero. Catalog edit does not write quantity.

See [erd.md](erd.md) for the diagram used in design reviews.

## PII

`customer_requests.contact_ciphertext` is Fernet output. Application backups decrypt contacts into a file that must be treated as sensitive and stored with the same access rules as the database.

## Migrations

Alembic revision `0001_initial` creates the schema from SQLAlchemy metadata. Application startup also calls `create_all` so a fresh SQLite laptop copy works without an extra command.
