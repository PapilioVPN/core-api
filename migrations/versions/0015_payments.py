"""Store manual retail transfers and their review outcome.

Revision ID: 0015
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op

revision = "0015"
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
        sa.Column("card_id", sa.BigInteger(), nullable=True),
        sa.Column("bank_id", sa.BigInteger(), nullable=False),
        sa.Column("card_last4", sa.String(4), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("reference", sa.String(64), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("reviewer_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["card_id"], ["tbl_payment_cards.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["bank_id"], ["tbl_banks.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_payments_customer", "tbl_payments", ["customer_id", "id"]
    )
    op.create_index("ix_payments_card", "tbl_payments", ["card_id", "id"])
    op.create_index("ix_payments_status", "tbl_payments", ["status", "id"])
    op.create_index("ix_tbl_payments_bank_id", "tbl_payments", ["bank_id"])


def downgrade() -> None:
    op.drop_table("tbl_payments")
