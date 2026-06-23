# ADR 004 — Snapshot Threshold

**Date:** 2024-01-01  
**Status:** Accepted

## Context

Event sourcing requires replaying all events to rebuild aggregate state on every
command. For accounts with thousands of transactions this becomes expensive.

## Decision

Take a snapshot every **20 events** (`SNAPSHOT_THRESHOLD = 20` in `aggregate.py`).
On load, fetch the latest snapshot then replay only the delta (events after the
snapshot version).

## Consequences

**Positive**
- Replay cost is O(20) worst case regardless of account age
- Snapshot threshold is a single constant — easy to tune per environment

**Negative**
- Extra write on every 20th command (negligible)
- Snapshot schema must be versioned if aggregate structure changes

## Alternatives considered

- **No snapshots** — fine for a portfolio project with low event counts, but
  wrong to demo; the snapshot code shows interviewers you understand the
  performance implications
- **Time-based snapshots** — harder to reason about; event-count is simpler
  and deterministic