"""Store the original quote for a cryptocurrency payment.

Revision ID: 0039
Revises: 0038
"""

import sqlalchemy as sa
from alembic import op

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_crypto_payments", sa.Column("quote_amount", sa.Numeric())
    )
    op.add_column(
        "tbl_crypto_payments", sa.Column("quote_currency", sa.String(3))
    )
    op.add_column("tbl_crypto_payments", sa.Column("quote_rate", sa.Numeric()))


def downgrade() -> None:
    op.drop_column("tbl_crypto_payments", "quote_rate")
    op.drop_column("tbl_crypto_payments", "quote_currency")
    op.drop_column("tbl_crypto_payments", "quote_amount")
