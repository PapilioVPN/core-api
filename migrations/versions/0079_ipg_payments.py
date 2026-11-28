"""Store online payments and their provider link outcome.

Revision ID: 0079
Revises: 0078
"""

import sqlalchemy as sa
from alembic import op

revision = "0079"
down_revision = "0078"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_ipg_payments",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "gateway_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_ipg_gateways.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reference", sa.String(128)),
        sa.Column("pay_url", sa.Text()),
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
            "reference",
            name=op.f("uq_tbl_ipg_payments_gateway_id_reference"),
        ),
    )


def downgrade() -> None:
    op.drop_table("tbl_ipg_payments")
