"""Prevent overlapping reservations of the same automatic transfer amount.

Revision ID: 0066
Revises: 0065
"""

import sqlalchemy as sa
from alembic import op

revision = "0066"
down_revision = "0065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_tbl_card_payments_payable_amount",
        "tbl_card_payments",
        ["payable_amount"],
    )
    op.execute(
        sa.text("""
            ALTER TABLE tbl_card_payments
            ADD CONSTRAINT excl_card_payments_amount EXCLUDE USING gist (
                numrange(payable_amount, payable_amount, '[]') WITH =,
                tstzrange(created_at, expires_at, '[)') WITH &&
            ) WHERE (mode = 'auto' AND payable_amount IS NOT NULL
                     AND expires_at IS NOT NULL)
        """)
    )


def downgrade() -> None:
    op.drop_constraint("excl_card_payments_amount", "tbl_card_payments")
    op.drop_index(
        "ix_tbl_card_payments_payable_amount", table_name="tbl_card_payments"
    )
