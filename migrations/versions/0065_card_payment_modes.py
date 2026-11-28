"""Add automatic card payment terms to the existing payments table.

Revision ID: 0065
Revises: 0064
"""

import sqlalchemy as sa
from alembic import op

revision = "0065"
down_revision = "0064"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_card_payments",
        sa.Column(
            "mode", sa.String(6), server_default="manual", nullable=False
        ),
    )
    op.alter_column("tbl_card_payments", "mode", server_default=None)
    op.add_column(
        "tbl_card_payments", sa.Column("payable_amount", sa.BigInteger())
    )
    op.add_column("tbl_card_payments", sa.Column("code", sa.String(5)))
    op.add_column(
        "tbl_card_payments",
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.alter_column("tbl_card_payments", "receipt_url", nullable=True)
    op.create_index("ix_tbl_card_payments_code", "tbl_card_payments", ["code"])


def downgrade() -> None:
    # The old schema cannot represent a payment without a receipt.
    op.alter_column("tbl_card_payments", "receipt_url", nullable=False)
    op.drop_index("ix_tbl_card_payments_code", table_name="tbl_card_payments")
    for column in ("expires_at", "code", "payable_amount", "mode"):
        op.drop_column("tbl_card_payments", column)
