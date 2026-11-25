"""Store gateway icons and encrypted JSON connection settings.

Revision ID: 0032
Revises: 0031
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tbl_crypto_gateways", sa.Column("icon_url", sa.String(255)))
    op.create_table(
        "tbl_crypto_gateway_configs",
        sa.Column(
            "gateway_id",
            sa.BigInteger(),
            sa.ForeignKey("tbl_crypto_gateways.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("config", JSONB(), nullable=False),
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


def downgrade() -> None:
    op.drop_table("tbl_crypto_gateway_configs")
    op.drop_column("tbl_crypto_gateways", "icon_url")
