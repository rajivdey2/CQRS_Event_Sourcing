"""001 create events and snapshots tables

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMPTZ

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "events",
        sa.Column("id",             UUID,        server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("stream_id",      UUID,        nullable=False),
        sa.Column("version",        sa.Integer,  nullable=False),
        sa.Column("event_type",     sa.Text,     nullable=False),
        sa.Column("payload",        JSONB,        nullable=False),
        sa.Column("correlation_id", UUID,        nullable=True),
        sa.Column("causation_id",   UUID,        nullable=True),
        sa.Column("occurred_at",    TIMESTAMPTZ, server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("stream_id", "version", name="uq_stream_version"),
    )
    op.create_index("idx_events_stream_id",   "events", ["stream_id", "version"])
    op.create_index("idx_events_event_type",  "events", ["event_type"])
    op.create_index("idx_events_occurred_at", "events", ["occurred_at"])

    op.create_table(
        "snapshots",
        sa.Column("id",             UUID,        server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("stream_id",      UUID,        nullable=False),
        sa.Column("version",        sa.Integer,  nullable=False),
        sa.Column("aggregate_type", sa.Text,     nullable=False),
        sa.Column("state",          JSONB,        nullable=False),
        sa.Column("created_at",     TIMESTAMPTZ, server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("stream_id", "version", name="uq_snapshot_stream_version"),
    )
    op.create_index("idx_snapshots_stream_id", "snapshots", ["stream_id", sa.text("version DESC")])


def downgrade():
    op.drop_table("snapshots")
    op.drop_table("events")