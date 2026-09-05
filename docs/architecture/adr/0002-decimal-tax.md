# ADR 0002 — Money as Decimal; tax from environment

**Status:** Accepted  
**Date:** 2026-08-25  
**Deciders:** Richard Mora (POS), Stephen Merten (QA)

## Context

Definition of Done requires accurate tax and totals. Floating-point money fails that requirement.

## Decision

All currency values are `Decimal` quantized to cents. Tax is `TAX_RATE_BPS` in the environment (725 = 7.25%), not a literal inside checkout.

## Consequences

Tests can pin exact cents (for example $16.00 at 725 bps → $1.16 tax). Changing municipal tax is a config change, not a code change.
