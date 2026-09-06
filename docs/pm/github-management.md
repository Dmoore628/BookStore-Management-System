# GitHub Ecosystem Management

## 1. Automated Actions (`.github/workflows/ci.yml`)
- **Linting:** Runs `ruff`.
- **Typing:** Runs `mypy`.
- **Security:** Runs `bandit` and `pip-audit`.
- **Testing:** Runs `pytest`.

## 2. GitHub Project Management
- **Boards:** Track tasks via `docs/pm/backlog.md` and `docs/pm/standups/`.
- **Templates:**
  - `/ISSUE_TEMPLATE/story.md`: For tracking features.
  - `/PULL_REQUEST_TEMPLATE.md`: Standardized review template.

## 3. Branching Strategy & Rulesets
- **Branches:** `main` (Production), `develop` (Integration).
- **Rulesets:**
  - Branch protection on `main` and `develop`:
    - Require pull request reviews before merging.
    - Require status checks to pass before merging.
    - Linear history (no merges, rebase only).
    - Signed commits required.

## 4. Security & Access
- **Advanced Security:** CodeQL scanning enabled.
- **CODEOWNERS:** Defined in `.github/CODEOWNERS` for automated review routing.
- **Environments:** `production` and `staging` configured on GitHub (tied to Vercel/Neon environments).
