"""Store crypto payment terms and gateway invoice identities.

Revision ID: 0029
Revises: 0028
"""

import sqlalchemy as sa
from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_crypto_payments",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("gateway", sa.String(55), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("price_amount", sa.Numeric(), nullable=False),
        sa.Column("price_currency", sa.String(64), nullable=False),
        sa.Column("pay_currency", sa.String(64)),
        sa.Column("invoice_id", sa.String(255)),
        sa.Column("invoice_url", sa.Text()),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "gateway", "invoice_id", name="uq_crypto_payment_invoice"
        ),
    )


def downgrade() -> None:
    op.drop_table("tbl_crypto_payments")
