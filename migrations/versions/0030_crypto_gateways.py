"""Manage crypto gateways independently of payment records.

Revision ID: 0030
Revises: 0029
"""

import sqlalchemy as sa
from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_crypto_gateways",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("key", sa.String(55), nullable=False, unique=True),
        sa.Column("title", sa.String(55), nullable=False),
        sa.Column("kind", sa.String(55)),
        sa.Column("price_currency", sa.String(64)),
        sa.Column("pay_currency", sa.String(64)),
        sa.Column("rial_rate", sa.Numeric(24, 8)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
    )
    op.execute(
        """
        INSERT INTO tbl_crypto_gateways (key, title, is_active)
        SELECT DISTINCT gateway, gateway, false FROM tbl_crypto_payments
        """
    )
    op.add_column(
        "tbl_crypto_payments", sa.Column("gateway_id", sa.BigInteger())
    )
    op.execute(
        """
        UPDATE tbl_crypto_payments AS payment
        SET gateway_id = gateway.id
        FROM tbl_crypto_gateways AS gateway
        WHERE payment.gateway = gateway.key
        """
    )
    op.alter_column("tbl_crypto_payments", "gateway_id", nullable=False)
    op.create_foreign_key(
        "fk_crypto_payments_gateway",
        "tbl_crypto_payments",
        "tbl_crypto_gateways",
        ["gateway_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "uq_crypto_payment_invoice", "tbl_crypto_payments", type_="unique"
    )
    op.create_unique_constraint(
        "uq_crypto_payment_invoice",
        "tbl_crypto_payments",
        ["gateway_id", "invoice_id"],
    )
    op.drop_column("tbl_crypto_payments", "gateway")


def downgrade() -> None:
    op.add_column("tbl_crypto_payments", sa.Column("gateway", sa.String(55)))
    op.execute(
        """
        UPDATE tbl_crypto_payments AS payment
        SET gateway = gateway.key
        FROM tbl_crypto_gateways AS gateway
        WHERE payment.gateway_id = gateway.id
        """
    )
    op.alter_column("tbl_crypto_payments", "gateway", nullable=False)
    op.drop_constraint(
        "uq_crypto_payment_invoice", "tbl_crypto_payments", type_="unique"
    )
    op.create_unique_constraint(
        "uq_crypto_payment_invoice",
        "tbl_crypto_payments",
        ["gateway", "invoice_id"],
    )
    op.drop_constraint(
        "fk_crypto_payments_gateway", "tbl_crypto_payments", type_="foreignkey"
    )
    op.drop_column("tbl_crypto_payments", "gateway_id")
    op.drop_table("tbl_crypto_gateways")
