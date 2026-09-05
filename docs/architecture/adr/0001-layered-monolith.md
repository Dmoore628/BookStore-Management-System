# ADR 0001 — Layered monolith, not microservices

**Status:** Accepted  
**Date:** 2026-08-24  
**Deciders:** Damian J. Moore, Richard Mora, Stephen Merten

## Context

The vision document asked for desktop software with three modules and one central database. The team is three people and two sprints.

## Decision

Ship one FastAPI process: HTML staff console + JSON API + SQLAlchemy services. PostgreSQL in staging/production, SQLite in tests.

## Consequences

We can finish BMS-1 through BMS-8 with honest test coverage. We cannot claim independent deployable services. A later WebView wrapper can still present the same localhost UI as a “desktop” icon.
