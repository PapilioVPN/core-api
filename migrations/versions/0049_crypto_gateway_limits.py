"""Add optional rial limits to gateway accounts.

Revision ID: 0049
Revises: 0047
"""

import sqlalchemy as sa
from alembic import op

revision = "0049"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_crypto_gateways", sa.Column("min_amount", sa.BigInteger())
    )
    op.add_column(
        "tbl_crypto_gateways", sa.Column("max_amount", sa.BigInteger())
    )


def downgrade() -> None:
    op.drop_column("tbl_crypto_gateways", "max_amount")
    op.drop_column("tbl_crypto_gateways", "min_amount")
