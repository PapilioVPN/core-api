"""Store shared pricing-currency rates in Iranian rials.

Revision ID: 0037
Revises: 0036
"""

import sqlalchemy as sa
from alembic import op

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_crypto_rates",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("currency", sa.String(3), nullable=False, unique=True),
        sa.Column("rial_rate", sa.Numeric(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tbl_crypto_rates")
