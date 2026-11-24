"""Install native Outbox storage.

Revision ID: 0021
Revises: 0020
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Install native pending and terminal-failure storage."""
    op.create_table(
        "event_outbox",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("queue", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.LargeBinary(), nullable=False),
        sa.Column(
            "headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "attempts_count",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "deliveries_count",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "first_attempt_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "last_attempt_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acquired_token", sa.Uuid(), nullable=True),
        sa.Column("timer_id", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "(acquired_token IS NULL) = (acquired_at IS NULL)",
            name="event_outbox_lease_ck",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "event_outbox_leased_idx",
        "event_outbox",
        ["queue", "next_attempt_at", "id"],
        unique=False,
        postgresql_where=sa.text("acquired_token IS NOT NULL"),
    )
    op.create_index(
        "event_outbox_pending_idx",
        "event_outbox",
        ["queue", "next_attempt_at", "id"],
        unique=False,
        postgresql_where=sa.text("acquired_token IS NULL"),
    )
    op.create_index(
        "event_outbox_timer_id_uq",
        "event_outbox",
        ["queue", "timer_id"],
        unique=True,
        postgresql_where=sa.text("timer_id IS NOT NULL"),
    )
    op.create_table(
        "event_outbox_dlq",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("original_id", sa.BigInteger(), nullable=False),
        sa.Column("queue", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.LargeBinary(), nullable=False),
        sa.Column(
            "headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("deliveries_count", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "failed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("failure_reason", sa.String(length=64), nullable=False),
        sa.Column("last_exception", sa.String(), nullable=True),
        sa.Column("timer_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "event_outbox_dlq_queue_failed_idx",
        "event_outbox_dlq",
        ["queue", "failed_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the native event queue tables."""
    op.drop_table("event_outbox_dlq")
    op.drop_table("event_outbox")
