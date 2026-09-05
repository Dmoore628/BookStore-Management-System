# Business guide — for the bookstore owner

Ledger & Spine is the staff console that sits on the store PC. It is not a public web shop. Customers never create accounts.

## What you replaced

| Paper | Software |
| --- | --- |
| Stock cards | Catalog + quantity ledger |
| Register tape / day sheet | Checkout + day drawer |
| Order notebook | Supplier orders + special-order list |

## People and logins

Three example staff accounts exist after seeding:

| Username | Role | Typical use |
| --- | --- | --- |
| damian | owner | Settings, staff accounts, backups, day drawer |
| richard | manager | Catalog, receiving, sales review, contact details |
| stephen | cashier | Selling and taking special-order names |

Passwords live in the environment file on the store PC, not in GitHub. Change the seed passwords the first evening you go live.

## Tax

Sales tax is a store policy number: `TAX_RATE_BPS` (725 means 7.25%). Changing tax does not require a programmer to edit checkout code.

## Data protection

- Staff passwords are stored as bcrypt hashes.
- Customer phone/email on special orders is encrypted. Cashiers cannot decrypt it.
- Sales tickets are only listed for manager and owner roles.
- Backups are JSON files on disk. They contain decrypted contact data so you can recover after a disk failure — treat the backup folder like the cash office, not like a shared desktop.

If you lose the encryption key, old contacts in the database cannot be read. Keep the key with the same care as the alarm code.

## Staging vs the live store

Software is tried on the **staging** copy (same program, separate database) before it is copied to **production** (`main` on GitHub). Damian merges staging to production only after the release checklist is ticked.

## Rollback

Keep the previous Docker image or the previous `main` commit. Database tables in 1.0.0 do not require a destructive migrate to roll back the application. If data is wrong, restore the last backup JSON and re-enter sales taken after that file was written.
