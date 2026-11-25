"""Attach a hosted invoice to its cryptocurrency payment.

Revision ID: 0041
Revises: 0040
"""

import sqlalchemy as sa
from alembic import op

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_crypto_payments", sa.Column("invoice_id", sa.String(64))
    )
    op.add_column("tbl_crypto_payments", sa.Column("invoice_url", sa.Text()))


def downgrade() -> None:
    op.drop_column("tbl_crypto_payments", "invoice_url")
    op.drop_column("tbl_crypto_payments", "invoice_id")
