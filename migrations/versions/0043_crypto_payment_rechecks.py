"""Index outstanding issued payments by their last scheduled attempt.

Revision ID: 0043
Revises: 0042
"""

import sqlalchemy as sa
from alembic import op

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_crypto_payments",
        sa.Column("last_check_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_crypto_payments_due",
        "tbl_crypto_payments",
        [sa.text("last_check_at NULLS FIRST"), "id"],
        postgresql_where=sa.text(
            "confirmed_at IS NULL AND invoice_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_crypto_payments_due", table_name="tbl_crypto_payments")
    op.drop_column("tbl_crypto_payments", "last_check_at")
