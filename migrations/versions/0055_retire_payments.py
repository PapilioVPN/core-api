"""Remove the retired bank and crypto payment schemas.

Revision ID: 0055
Revises: 0054
"""

from alembic import op

revision = "0055"
down_revision = "0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("tbl_deposits", "payment_id")
    op.drop_table("tbl_payments")
    op.drop_table("tbl_crypto_payments")


def downgrade() -> None:
    raise NotImplementedError("Retired payment data cannot be restored.")
