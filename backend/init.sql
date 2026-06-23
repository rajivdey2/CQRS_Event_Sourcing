CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── EVENT STORE ────────────────────────────────────────────────────────────
-- Append-only. Never UPDATE or DELETE rows here.
-- stream_id  = the aggregate ID (account UUID)
-- version    = monotonically increasing per stream (starts at 1)
-- UNIQUE(stream_id, version) is the entire optimistic-concurrency mechanism
CREATE TABLE IF NOT EXISTS events (
    id           UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    stream_id    UUID        NOT NULL,
    version      INT         NOT NULL,
    event_type   TEXT        NOT NULL,
    payload      JSONB       NOT NULL,
    correlation_id UUID,                     -- groups all events from one request
    causation_id   UUID,                     -- points to the parent event id
    occurred_at  TIMESTAMPTZ DEFAULT now()   NOT NULL,
    CONSTRAINT uq_stream_version UNIQUE (stream_id, version)
);

CREATE INDEX IF NOT EXISTS idx_events_stream_id    ON events (stream_id, version);
CREATE INDEX IF NOT EXISTS idx_events_event_type   ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_occurred_at  ON events (occurred_at);

-- ─── SNAPSHOT STORE ─────────────────────────────────────────────────────────
-- Stores serialised aggregate state every N events so replay stays fast.
CREATE TABLE IF NOT EXISTS snapshots (
    id           UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    stream_id    UUID        NOT NULL,
    version      INT         NOT NULL,       -- version AT time of snapshot
    aggregate_type TEXT      NOT NULL,
    state        JSONB       NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT now()   NOT NULL,
    CONSTRAINT uq_snapshot_stream_version UNIQUE (stream_id, version)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_stream_id ON snapshots (stream_id, version DESC);

-- ─── READ MODEL: account balance ─────────────────────────────────────────────
-- Updated by the balance projector after every command.
-- Intentionally denormalised for O(1) balance lookups.
CREATE TABLE IF NOT EXISTS account_balance_view (
    account_id   UUID        PRIMARY KEY,
    owner_name   TEXT        NOT NULL,
    balance      NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency     CHAR(3)     NOT NULL DEFAULT 'USD',
    status       TEXT        NOT NULL DEFAULT 'active',  -- active | closed
    version      INT         NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- ─── READ MODEL: transaction history ─────────────────────────────────────────
-- Append-only projection; one row per financial event.
CREATE TABLE IF NOT EXISTS transaction_history_view (
    id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id    UUID        NOT NULL,
    event_id      UUID        NOT NULL UNIQUE,   -- idempotency: skip if seen
    event_type    TEXT        NOT NULL,           -- Deposited | Withdrawn | Opened
    amount        NUMERIC(18,2),
    balance_after NUMERIC(18,2),
    description   TEXT,
    occurred_at   TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tx_account_id   ON transaction_history_view (account_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_tx_event_id     ON transaction_history_view (event_id);