# Repository structure

A map of the repo so a new contributor can find anything in under a minute. The
guiding principle is **separation of concerns**: pure domain logic never imports
HTTP or UI code, and configuration is never hardcoded.

```
BookStore-Management-System/
├── README.md                  # Front door: what/why + quick start
├── LICENSE  CONTRIBUTING.md  SECURITY.md   # Project governance
├── pyproject.toml             # Package metadata, deps, tool config (ruff/mypy/pytest/coverage)
├── .env.example               # Every configuration key, documented (no secrets committed)
├── .pre-commit-config.yaml  .editorconfig  # Local quality gates
├── Dockerfile  docker-compose*.yml         # Containerized dev / staging / prod
├── alembic.ini  alembic/      # Database migrations
│
├── src/bookstore/             # Application package (import root)
│   ├── config.py              #   Settings — all values from the environment
│   ├── database.py            #   Engine, session factory, declarative Base
│   ├── security.py            #   Password hashing + PII encryption
│   ├── models/                #   ORM entities + enums (the data model)
│   ├── schemas/               #   Pydantic request/response models (the API contract)
│   ├── services/              #   Domain logic — pure, typed, no HTTP knowledge
│   │                          #     money · inventory · cart · checkout · sales
│   │                          #     orders · requests · auth · backup
│   ├── api/                   #   FastAPI dependencies + thin routers over services
│   ├── web/                   #   Server-rendered UI (Jinja templates, htmx, design tokens)
│   └── main.py                #   App factory + ASGI entrypoint
│
├── tests/                     # Test suite mirrors the package
│   ├── conftest.py            #   Shared fixtures (isolated in-memory DB, factories)
│   ├── test_*.py              #   Unit + integration tests
│   ├── property/              #   Hypothesis property-based tests
│   ├── contract/              #   Schemathesis OpenAPI contract tests
│   ├── e2e/                   #   Playwright end-to-end + accessibility + visual
│   └── load/                  #   k6 performance scripts
│
├── scripts/                   # Operational scripts (seed data, doc generation, packaging)
│
└── docs/                      # All documentation
    ├── architecture/          #   System design, ADRs, ERD, diagrams
    ├── process/               #   Scrum: backlog, sprints, standups, retros, traceability
    ├── management/            #   PM: charter, RACI, risk register, roadmap, NFRs, metrics
    ├── qa/                    #   Test strategy, security scan results
    ├── user/                  #   Staff manual, business guide
    ├── course-source/         #   Original CS491/CS492 course artifacts (source of truth)
    ├── project-document/      #   Consolidated Project Document deliverable
    ├── presentation/          #   Final deck + peer-review templates
    └── superpowers/           #   Design spec + implementation plan
```

## Dependency direction

```
web ─┐
     ├─▶ api ─▶ services ─▶ models ─▶ database
schemas ┘                    │
                             ▼
              config · security (shared primitives)
```

Nothing in `services/` imports from `api/` or `web/`. That keeps the business
rules testable in isolation and portable if the delivery mechanism ever changes.
