"""Index outstanding crypto payments by their last check.

Revision ID: 0033
Revises: 0032
"""

import sqlalchemy as sa
from alembic import op

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_crypto_payments",
        sa.Column("checked_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_crypto_payments_recheck",
        "tbl_crypto_payments",
        [sa.text("coalesce(checked_at, created_at)"), "id"],
        postgresql_where=sa.text(
            "invoice_id IS NOT NULL AND status IN ('pending', 'partial')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_crypto_payments_recheck", table_name="tbl_crypto_payments"
    )
    op.drop_column("tbl_crypto_payments", "checked_at")
