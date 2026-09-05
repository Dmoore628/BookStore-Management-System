# Release checklist (`staging` → `main`)

Product Owner: Damian J. Moore  
QA: Stephen Park  
Scrum Master: Richard Hale  

- [ ] `develop` merged to `staging`; Actions CI green on both.
- [ ] Staging Compose stack started against PostgreSQL.
- [ ] Owner login works; Richard manager login works; Stephen cashier login works.
- [ ] Cash sale: stock drops; change due is correct for the configured tax rate.
- [ ] Card sale appears on the day drawer split.
- [ ] Receive a pending supplier order; on-hand quantity increases.
- [ ] Special-order contact hidden from cashier, visible to manager.
- [ ] Backup JSON written; path recorded.
- [ ] No `.env` or key material in the Git diff.
- [ ] Staff manual current.
- [ ] Damian signs off. Merge `staging` into `main`. Tag `v1.0.0`.
