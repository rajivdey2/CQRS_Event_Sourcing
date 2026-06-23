# ADR 003 — In-Process Event Bus vs Kafka

**Date:** 2024-01-01  
**Status:** Accepted (phase 1); Kafka migration planned for phase 2

## Context

After persisting events, projectors must be notified. We could publish to
Kafka for full async decoupling, or use an in-process bus for simplicity.

## Decision

Start with `InProcessEventBus` (see `infrastructure/event_bus.py`).
The bus and its Kafka replacement implement the same `publish()` / `subscribe()`
interface, so command handlers require zero changes when we swap.

## Consequences

**Positive**
- No Kafka infra to run locally — `docker-compose up` is one command
- Zero network hops: projectors update in the same request lifecycle
- Interface is stable — migration to Kafka is a one-file swap

**Negative**
- Projector failure doesn't retry — a crashing projector is silently skipped
  (`return_exceptions=True` in `gather`)
- No durable delivery guarantee: if the process dies after DB commit but
  before projector runs, the read model lags until next rebuild

## Migration path to Kafka (phase 2)

1. Add `KafkaEventBus` implementing the same interface
2. Command handlers publish to Kafka topic after `append_events()`
3. Projectors become Kafka consumers (separate process or thread)
4. Outbox pattern eliminates the dual-write gap