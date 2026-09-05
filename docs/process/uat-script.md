# UAT script (Stephen Park)

Run on staging after `develop` is merged. Sign in as each role.

1. Owner (damian): add a staff manager if missing; create a book; open day drawer (may be zero).
2. Manager (richard): edit the book price; do not change quantity on the edit form.
3. Cashier (stephen): sell one copy cash with known tender; confirm change; confirm stock dropped by one.
4. Cashier: try to open day drawer — must be denied.
5. Manager: log supplier order for that title; mark received; stock up by ordered qty.
6. Cashier: log a special order with a phone number; confirm the number is not visible on the cashier screen.
7. Manager: confirm the phone number is visible; set status to ordered.
8. Owner: write a backup; confirm a new file appears in the backup directory.

Pass/fail recorded on the release PR.
