# Ledger — CQRS + Event Sourcing

A production-grade bank account ledger demonstrating **CQRS** (Command Query Responsibility Segregation) and **Event Sourcing** patterns, built with FastAPI + React.

![Architecture](docs/architecture.png)

## Live Demo

> Vercel -> [https://cqrs-event-sourcing-q1vzpzcc9-rajivdey2s-projects.vercel.app](https://cqrs-event-sourcing-q1vzpzcc9-rajivdey2s-projects.vercel.app)
> API docs -> [https://cqrs-event-sourcing.onrender.com/docs](https://cqrs-event-sourcing.onrender.com/docs)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT                               │
│   POST /commands/*          GET /queries/*                  │
└──────────────┬───────────────────────┬──────────────────────┘
               │                       │
        COMMAND SIDE             QUERY SIDE
               │                       │
    ┌──────────▼──────────┐   ┌────────▼────────┐
    │  Command Handler    │   │  Query Handler  │
    │  (validates intent) │   │  (read-only)    │
    └──────────┬──────────┘   └────────▲────────┘
               │                       │
    ┌──────────▼──────────┐   ┌────────┴────────┐
    │ Domain Aggregate    │   │  Read Models    │
    │ (business logic)    │   │  balance_view   │
    └──────────┬──────────┘   │  tx_history     │
               │              └────────▲────────┘
    ┌──────────▼──────────┐            │
    │    Event Store      │────────────┤ (projectors)
    │  (append-only PG)   │   Event Bus│
    └─────────────────────┘            │
                             ┌─────────┴────────┐
                             │  Snapshot Store  │
                             │  (every 20 evts) │
                             └──────────────────┘
```

### Key design decisions

| Decision | Choice | Why |
|---|---|---|
| Concurrency | `UNIQUE(stream_id, version)` | Zero-overhead optimistic locking — Postgres rejects duplicate versions |
| Event bus | In-process (phase 1) | No infra overhead; same interface as Kafka for easy swap |
| Snapshots | Every 20 events | Avoids O(N) replay on long-lived accounts |
| Read models | Denormalised tables | O(1) balance lookup — no joins, no aggregate replay on reads |
| Projection rebuild | Admin replay endpoint | Wipe + re-run all events → any new projection gets history for free |

See [`docs/adr/`](docs/adr/) for full Architecture Decision Records.

---

## Stack

**Backend** — Python 3.12, FastAPI, SQLAlchemy (async), asyncpg, PostgreSQL 16, Alembic  
**Frontend** — React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts

---

## Quick start

### One command (Docker)

```bash
docker compose up
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Local development

```bash
# Terminal 1 — Postgres
docker compose up postgres -d

# Terminal 2 — Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload

# Terminal 3 — Frontend
cd frontend
npm install
npm run dev           # → http://localhost:5173
```

---

## API

### Commands (write side)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/commands/accounts` | Open a new account |
| `POST` | `/api/commands/accounts/{id}/deposit` | Deposit money |
| `POST` | `/api/commands/accounts/{id}/withdraw` | Withdraw money |
| `POST` | `/api/commands/accounts/{id}/close` | Close account |

### Queries (read side)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/queries/accounts` | List all accounts |
| `GET` | `/api/queries/accounts/{id}/balance` | Current balance (read model) |
| `GET` | `/api/queries/accounts/{id}/transactions` | Transaction history |
| `GET` | `/api/queries/accounts/{id}/events` | Raw event stream |

### Admin

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/admin/rebuild-projection` | Wipe + replay all events |
| `GET`  | `/api/admin/stats` | Event store metrics |

---

## What makes this production-grade

**Optimistic concurrency** — `UNIQUE(stream_id, version)` means two simultaneous deposits on the same account resolve at the DB level with zero locking. One wins, one gets 409 and retries.

**Idempotent projectors** — `ON CONFLICT (event_id) DO NOTHING` means replaying the same event twice never creates duplicate transaction rows.

**Projection rebuild** — `POST /api/admin/rebuild-projection` truncates read models and replays the entire event history. Add a new projection next month and it gets full history for free.

**Correlation + causation IDs** — every event carries `correlation_id` (groups all events from one request) and `causation_id` (points to parent event). Full distributed trace without Jaeger.

**Snapshot optimisation** — aggregates with >20 events save a state snapshot. Next load starts from the snapshot + delta, keeping replay O(1) regardless of account age.

---

## Running tests

```bash
cd backend
pytest tests/unit/ -v                    # pure domain logic, no DB
pytest tests/integration/ -v             # full HTTP roundtrip
pytest tests/integration/test_concurrency.py -v   # race condition test
```

---

## Architecture Decision Records

- [ADR 001 — Why Event Sourcing](docs/adr/001-why-event-sourcing.md)
- [ADR 002 — Optimistic Concurrency](docs/adr/002-optimistic-concurrency.md)
- [ADR 003 — In-Process vs Kafka](docs/adr/003-in-process-vs-kafka.md)
