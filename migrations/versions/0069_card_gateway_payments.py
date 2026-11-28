"""Store hosted card payments and provider links.

Revision ID: 0069
Revises: 0068
"""

import sqlalchemy as sa
from alembic import op

revision = "0069"
down_revision = "0068"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_card_gateway_payments",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "gateway_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_card_gateways.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("slug", sa.Text()),
        sa.Column("pay_url", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
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
            "gateway_id",
            "slug",
            name="tbl_card_gateway_payments_gateway_id_slug_key",
        ),
    )


def downgrade() -> None:
    op.drop_table("tbl_card_gateway_payments")
