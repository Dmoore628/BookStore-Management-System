# Product backlog

Source: `Final_Sprint_Planning_Document_v2.xlsx` (CS491/CS492). Original PO: Damian Jay Moore. Scrum Master and development team were blank in the workbook; this build assigns Richard Mora and Stephen Merten.

Sprints are two weeks.

## Sprint 1 — Foundation and inventory/POS

| ID | Title | Priority | Owner | Reviewer |
| --- | --- | --- | --- | --- |
| infra | GitHub, Compose, schema, Alembic | 0 | Damian | Richard |
| BMS-7 | User login and access control | 1 | Damian | Stephen |
| BMS-1 | Manage book inventory records | 1 | Richard | Damian |
| BMS-2 | Automatic stock quantity updates | 1 | Richard | Stephen |
| BMS-3 | Checkout calculation | 1 | Richard | Stephen |

## Sprint 2 — Orders, protection, release

| ID | Title | Priority | Owner | Reviewer |
| --- | --- | --- | --- | --- |
| BMS-4 | Daily cash/card sales log | 2 | Richard | Damian |
| BMS-5 | Supplier order tracking | 2 | Stephen | Richard |
| BMS-6 | Customer special-order requests | 2 | Stephen | Damian |
| BMS-8 | Protect sales and customer data | 2 | Damian / Stephen | Richard |
| ci-docs | Coverage gate, manuals, staging/prod | 2 | Damian / Stephen | Richard |

## Acceptance criteria (from the spreadsheet)

**BMS-1** All six fields (title, author, ISBN, price, quantity, shelf) can be entered and viewed. Records can be edited and retired (soft-delete so sales history remains).

**BMS-2** Quantity decreases on sale. Quantity increases on receiving stock. Cashiers do not type a new on-hand number to complete a sale.

**BMS-3** Subtotal, tax, and total are correct. Change due is calculated for cash. Ties to Definition of Done: accurate tax and totals.

**BMS-4** Every sale records date/time, amount, and payment method. A daily total can be viewed.

**BMS-5** An order can be logged with supplier, books, and status. Status can be updated to received.

**BMS-6** Request logs customer name, contact, and book. Status can move to ordered / fulfilled.

**BMS-7** Unique logins. Unauthenticated users cannot use the system.

**BMS-8** Customer contact is not stored as readable text. Only authorized staff view sales and contacts. Backups exist for retention and recovery.
