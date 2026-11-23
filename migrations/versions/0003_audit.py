"""Persist administrator audit records.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_audit_records",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("actor_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=True),
        sa.Column("scope_id", sa.BigInteger(), nullable=True),
        sa.Column("permissions", sa.SmallInteger(), nullable=True),
        sa.Column("count", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_audit_created", "tbl_audit_records", ["created_at", "id"]
    )
    op.create_index(
        "ix_audit_actor_created",
        "tbl_audit_records",
        ["actor_id", "created_at", "id"],
    )
    op.create_index(
        "ix_audit_action_created",
        "tbl_audit_records",
        ["action", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_table("tbl_audit_records")
