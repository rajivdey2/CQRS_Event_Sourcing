"""002 create read model view tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMPTZ

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_balance_view",
        sa.Column("account_id",   UUID,                  primary_key=True),
        sa.Column("owner_name",   sa.Text,               nullable=False),
        sa.Column("balance",      sa.Numeric(18, 2),     nullable=False, server_default="0"),
        sa.Column("currency",     sa.CHAR(3),            nullable=False, server_default="'USD'"),
        sa.Column("status",       sa.Text,               nullable=False, server_default="'active'"),
        sa.Column("version",      sa.Integer,            nullable=False, server_default="0"),
        sa.Column("last_updated", TIMESTAMPTZ,           server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "transaction_history_view",
        sa.Column("id",           UUID,              server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id",   UUID,              nullable=False),
        sa.Column("event_id",     UUID,              nullable=False, unique=True),
        sa.Column("event_type",   sa.Text,           nullable=False),
        sa.Column("amount",       sa.Numeric(18, 2), nullable=True),
        sa.Column("balance_after",sa.Numeric(18, 2), nullable=True),
        sa.Column("description",  sa.Text,           nullable=True),
        sa.Column("occurred_at",  TIMESTAMPTZ,       nullable=False),
    )
    op.create_index("idx_tx_account_id", "transaction_history_view", ["account_id", sa.text("occurred_at DESC")])
    op.create_index("idx_tx_event_id",   "transaction_history_view", ["event_id"])


def downgrade():
    op.drop_table("transaction_history_view")
    op.drop_table("account_balance_view")