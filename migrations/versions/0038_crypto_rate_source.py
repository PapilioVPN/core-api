"""Record the provenance of fetched crypto prices.

Revision ID: 0038
Revises: 0037
"""

import sqlalchemy as sa
from alembic import op

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tbl_crypto_rates", sa.Column("source", sa.String(24)))
    op.add_column(
        "tbl_crypto_rates",
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_column("tbl_crypto_rates", "fetched_at")
    op.drop_column("tbl_crypto_rates", "source")
