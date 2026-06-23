# ADR 002 — Optimistic Concurrency via DB Unique Constraint

**Date:** 2024-01-01  
**Status:** Accepted

## Context

Multiple requests for the same account could arrive simultaneously. We need
to prevent lost updates without using pessimistic locks (which kill throughput).

## Decision

Rely on the `UNIQUE(stream_id, version)` constraint in the `events` table.
Each command loads the current version, increments it, and tries to insert.
PostgreSQL rejects duplicate versions with an IntegrityError, which we surface
as HTTP 409 Conflict.

## Consequences

**Positive**
- Zero additional infrastructure — the constraint is free
- Atomic at the DB level — no race conditions
- Easy to understand and test (`test_concurrency.py`)

**Negative**
- Callers must handle 409 and retry with backoff
- Under high contention on one account the retry rate rises

## Alternatives considered

- **SELECT FOR UPDATE (pessimistic lock)** — simpler client, but serialises
  all writers for an account; unacceptable for high-traffic accounts
- **Redis distributed lock** — adds infrastructure dependency for a problem
  the DB already solves natively