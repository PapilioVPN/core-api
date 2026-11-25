"""Store cryptocurrency gateway accounts.

Revision ID: 0034
Revises: 0028
"""

import sqlalchemy as sa
from alembic import op

revision = "0034"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_crypto_gateways",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("kind", sa.String(55), nullable=False),
        sa.Column("title", sa.String(55), nullable=False),
        sa.Column("icon_url", sa.String(255)),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("tbl_crypto_gateways")
