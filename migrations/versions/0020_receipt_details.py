"""Store optional bank details observed on a receipt.

Revision ID: 0020
Revises: 0019
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tbl_receipts", sa.Column("amount", sa.BigInteger()))
    op.add_column(
        "tbl_receipts", sa.Column("paid_at", sa.DateTime(timezone=True))
    )
    op.add_column("tbl_receipts", sa.Column("tracking_code", sa.String(55)))
    op.add_column("tbl_receipts", sa.Column("reference_code", sa.String(55)))
    op.add_column("tbl_receipts", sa.Column("bank_name", sa.String(100)))
    op.add_column("tbl_receipts", sa.Column("source_last4", sa.String(4)))
    op.add_column("tbl_receipts", sa.Column("destination_last4", sa.String(4)))


def downgrade() -> None:
    op.drop_column("tbl_receipts", "destination_last4")
    op.drop_column("tbl_receipts", "source_last4")
    op.drop_column("tbl_receipts", "bank_name")
    op.drop_column("tbl_receipts", "reference_code")
    op.drop_column("tbl_receipts", "tracking_code")
    op.drop_column("tbl_receipts", "paid_at")
    op.drop_column("tbl_receipts", "amount")
