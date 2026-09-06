# Bookstore Management System - "Ledger & Spine"

A professional-grade Bookstore Management System, featuring a clean layered architecture, robust REST API, and a server-side rendered UI with HTMX.

## Architecture
- **Layered Monolith:** Strict separation between Domain Logic (`domain_services`), API Interface (`api_server`), and UI Layer (`web_client`).
- **DevOps:** Containerized for development (`docker-compose`); ready for serverless production (`vercel.json`).
- **CI/CD:** Automated linting, type checking, and testing pipelines (GitHub Actions).

## Getting Started
1. `pip install -e .`
2. `docker-compose up` (for Postgres development environment)
3. `pytest` (Note: DB harness requires further synchronization in CI environment).

## Project Management
- Tracked in `/docs/pm`.
- Professional standards enforced (PEP 8, strict typing).
