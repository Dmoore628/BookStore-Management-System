# Security

Report issues privately to the Product Owner (Damian J. Moore) — do not file a public GitHub issue that includes customer contact data.

## Built-in controls

- Passwords: bcrypt (cost 12).
- Sessions: signed cookies (`SECRET_KEY`), `SameSite=lax`, HTTPS-only in staging/production.
- Customer contact: Fernet (`ENCRYPTION_KEY`).
- Authorization: cashier < manager < owner.
- Secrets: environment variables only.

## Threat notes (small store, single PC)

This is not a public SaaS. The main risks are a stolen store PC, a shared login, and a backup folder left on a USB drive. Full-disk encryption of the PC and a locked backup directory matter as much as application code.
