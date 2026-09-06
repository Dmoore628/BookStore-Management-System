# Bookstore Management System - Architecture & DevOps Strategy

## 1. Professional Architecture (Separation of Concerns)
To ensure scalability and maintainability, the project is structured as a **Layered Monolith**:
- `src/bookstore/`:
  - `domain/`: Business logic, entities, and services (pure, no framework dependencies).
  - `api/`: REST interface (FastAPI routers, Pydantic schemas).
  - `web/`: UI Layer (Jinja2, HTMX, Static Assets).
  - `infrastructure/`: Database (SQLAlchemy), Security (Auth/Crypto), Config.

## 2. DevOps & CI/CD Pipeline
- **Local Development:** `docker-compose.yml` provides a production-parity environment (PostgreSQL, Redis).
- **GitHub Actions (CI):** `.github/workflows/ci.yml` runs on every PR:
  - Linting: `ruff` (enforcing PEP 8, complexity, security).
  - Static Analysis: `mypy` (strict type checking).
  - Testing: `pytest` (API integration, Domain units, Web components).
- **Deployment (Vercel):**
  - `vercel.json` configures the serverless environment.
  - Automatic deployment on `main` branch push.
  - Environment variables managed securely via Vercel Dashboard/CLI.

## 3. Security & Quality Assurance
- **Security:** `bandit` for SAST, `pip-audit` for dependency vulnerabilities, Fernet encryption for PII.
- **QA:** Mandatory ≥ 80% coverage gate. Playwright E2E tests for critical user journeys.
- **Project Management:** Tracked in GitHub Projects (`docs/pm/`).

## 4. Professional Entry Point
The root `/` route provides a clear, professional "Staff Dashboard" that serves as the entry point for the system.
