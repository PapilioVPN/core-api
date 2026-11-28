"""Store hosted card confirmations and authenticated provider deliveries.

Revision ID: 0073
Revises: 0072
"""

import sqlalchemy as sa
from alembic import op

revision = "0073"
down_revision = "0072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_card_gateway_payments", sa.Column("paid_amount", sa.BigInteger())
    )
    op.add_column(
        "tbl_card_gateway_payments", sa.Column("attempt_code", sa.String(255))
    )
    op.add_column(
        "tbl_card_gateway_payments",
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "tbl_card_gateway_deliveries",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "gateway_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_card_gateways.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("delivery_id", sa.String(255), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("attempt_code", sa.String(255), nullable=False),
        sa.Column("base_amount", sa.BigInteger(), nullable=False),
        sa.Column("paid_amount", sa.BigInteger(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "gateway_id",
            "delivery_id",
            name="tbl_card_gateway_deliveries_gateway_id_delivery_id_key",
        ),
    )


def downgrade() -> None:
    op.drop_table("tbl_card_gateway_deliveries")
    op.drop_column("tbl_card_gateway_payments", "confirmed_at")
    op.drop_column("tbl_card_gateway_payments", "attempt_code")
    op.drop_column("tbl_card_gateway_payments", "paid_amount")
