"""Store source-linked payments.

Revision ID: 0017
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_payments",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["tbl_customers.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_tbl_payments_customer", "tbl_payments", ["customer_id", "id"]
    )
    op.create_index(
        "ix_tbl_payments_source", "tbl_payments", ["source_id", "source", "id"]
    )
    op.create_index("ix_tbl_payments_status", "tbl_payments", ["status", "id"])


def downgrade() -> None:
    op.drop_table("tbl_payments")
