"""Create online payment gateway accounts.

Revision ID: 0076
Revises: 0075
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0076"
down_revision = "0075"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_ipg_gateways",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(55), nullable=False),
        sa.Column("icon_url", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
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
    op.drop_table("tbl_ipg_gateways")
