"""Store customer requests to top up wallet balances.

Revision ID: 0048
Revises: 0047
"""

import sqlalchemy as sa
from alembic import op

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_wallet_deposits",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["tbl_customers.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_wallet_deposits_customer",
        "tbl_wallet_deposits",
        ["customer_id", "id"],
    )


def downgrade() -> None:
    op.drop_table("tbl_wallet_deposits")
