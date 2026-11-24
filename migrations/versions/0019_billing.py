"""Store payments and their individual receipts.

Revision ID: 0019
Revises: 0018
"""

import sqlalchemy as sa
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_receipts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("image_url", sa.String(255), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_table(
        "tbl_payments",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "receipt_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_receipts.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("tbl_payments")
    op.drop_table("tbl_receipts")
