"""Remove the remaining Billing and Crypto tables.

Revision ID: 0057
Revises: 0056
"""

from alembic import op

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("tbl_ocr_requests_legacy")
    op.drop_table("tbl_receipts")
    op.drop_table("tbl_deposits")
    op.drop_table("tbl_payment_settings")
    op.drop_table("tbl_crypto_gateway_configs")
    op.drop_table("tbl_crypto_gateways")


def downgrade() -> None:
    raise NotImplementedError("Removed payment data cannot be restored.")
