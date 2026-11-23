"""Persist administrator sessions.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_admin_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("tbl_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_admin_sessions_user_seen",
        "tbl_admin_sessions",
        ["user_id", "last_seen_at", "id"],
    )
    op.create_index(
        "ix_tbl_admin_sessions_expires_at",
        "tbl_admin_sessions",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_table("tbl_admin_sessions")
