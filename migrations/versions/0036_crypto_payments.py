"""Store cryptocurrency payments before issuing invoices.

Revision ID: 0036
Revises: 0035
"""

import sqlalchemy as sa
from alembic import op

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_crypto_payments",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "gateway_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_crypto_gateways.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("amount", sa.BigInteger(), nullable=False),
    )
    op.create_index(
        "ix_tbl_crypto_payments_gateway_id",
        "tbl_crypto_payments",
        ["gateway_id"],
    )


def downgrade() -> None:
    op.drop_table("tbl_crypto_payments")
