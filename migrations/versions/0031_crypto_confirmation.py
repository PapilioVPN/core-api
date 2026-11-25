"""Store the authenticated provider payment that settled a crypto attempt.

Revision ID: 0031
Revises: 0030
"""

import sqlalchemy as sa
from alembic import op

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_crypto_payments", sa.Column("provider_payment_id", sa.String(64))
    )
    op.add_column(
        "tbl_crypto_payments",
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint(
        "uq_crypto_provider_payment",
        "tbl_crypto_payments",
        ["gateway_id", "provider_payment_id"],
    )


def downgrade() -> None:
    op.execute(
        "UPDATE tbl_crypto_payments SET status = 'pending' "
        "WHERE status = 'partial'"
    )
    op.drop_constraint(
        "uq_crypto_provider_payment", "tbl_crypto_payments", type_="unique"
    )
    op.drop_column("tbl_crypto_payments", "confirmed_at")
    op.drop_column("tbl_crypto_payments", "provider_payment_id")
