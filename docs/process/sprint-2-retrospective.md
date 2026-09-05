# Sprint 2 retrospective

**Dates:** 2026-09-04 through 2026-09-18 (planned window; implementation completed on the release candidate)  
**Facilitator:** Richard Mora  
**Attendees:** Damian J. Moore, Richard Mora, Stephen Merten

## Went well

- Supplier receive and POS decrement share `apply_stock_delta`, so BMS-2 stayed one rule instead of two.
- Fernet on customer contact plus role checks gave BMS-8 a test we can show the owner: cashier JSON has `contact: null`.
- Staging overlay (`SESSION_HTTPS_ONLY`) is a real difference from laptop HTTP, not a rename of `develop`.

## Could have gone better

- Backup JSON decrypts contacts by design. We should have labeled the backup directory “sensitive” in the staff manual on day one.

## Surprised us

- Soft-delete (retire title) was a better fit than hard delete once we realized sale lines keep a title snapshot but still point at `book_id`.

## Lessons

- Keep `main` a fast-forward from `staging`. Do not hotfix on production and “remember to cherry-pick.”
- Three people can cover PO, SM, and QA if every PR has a reviewer who did not write the code.
