"""Keep current crypto pricing rates only in Redis.

Revision ID: 0040
Revises: 0039
"""

import sqlalchemy as sa
from alembic import op

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("tbl_crypto_rates")


def downgrade() -> None:
    op.create_table(
        "tbl_crypto_rates",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("currency", sa.String(3), nullable=False, unique=True),
        sa.Column("rial_rate", sa.Numeric(), nullable=False),
        sa.Column("source", sa.String(24)),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
    )
