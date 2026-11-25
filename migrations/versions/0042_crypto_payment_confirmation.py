"""Record the provider operation that settled a crypto payment.

Revision ID: 0042
Revises: 0041
"""

import sqlalchemy as sa
from alembic import op

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_crypto_payments", sa.Column("settlement_id", sa.String(64))
    )
    op.add_column(
        "tbl_crypto_payments",
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_column("tbl_crypto_payments", "confirmed_at")
    op.drop_column("tbl_crypto_payments", "settlement_id")
