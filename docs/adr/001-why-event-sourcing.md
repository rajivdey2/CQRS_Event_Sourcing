# ADR 001 — Why Event Sourcing for the Ledger

**Date:** 2024-01-01  
**Status:** Accepted

## Context

A bank account ledger needs a complete, immutable audit trail. Users must be
able to see every transaction that ever occurred, and the system must be able
to answer "what was the balance at time T?" — something a mutable CRUD model
cannot do without extra audit tables bolted on.

## Decision

Store domain events as the source of truth (event sourcing). Current state
(balance) is a derived projection, not the primary record.

## Consequences

**Positive**
- Complete audit trail built-in — no extra work
- Time-travel queries possible (replay up to timestamp T)
- New read models can be added retroactively by replaying events
- Natural fit for CQRS: commands produce events, queries read projections

**Negative**
- More infrastructure than plain CRUD
- Balance lookup requires a read model (projector must be kept in sync)
- Schema evolution requires careful versioning of event payloads

## Alternatives considered

- **Audit log table alongside CRUD model** — duplicates data, two sources of
  truth can drift, harder to replay
- **CDC (Change Data Capture) from PostgreSQL WAL** — powerful but higher ops
  overhead; overkill for a portfolio project