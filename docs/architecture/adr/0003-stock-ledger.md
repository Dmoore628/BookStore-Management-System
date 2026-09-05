# ADR 0003 — Quantity only through stock_movements

**Status:** Accepted  
**Date:** 2026-08-26  
**Deciders:** Richard Hale, Damian J. Moore

## Context

BMS-2 forbids cashiers typing a new on-hand count to complete a sale. Paper cards failed because the number and the sale were two different notebooks.

## Decision

`books.quantity` is a cache. Every change inserts `stock_movements` with reason `sale`, `receipt`, `initial`, or `correction`. Checkout decrements; receiving increments; managers may correct after a cycle count.

## Consequences

Sales history and the shelf number can be reconciled. Catalog edit does not touch quantity.
