"""Store per-account cryptocurrency gateway settings.

Revision ID: 0035
Revises: 0034
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_crypto_gateway_configs",
        sa.Column(
            "gateway_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_crypto_gateways.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("config", JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tbl_crypto_gateway_configs")
