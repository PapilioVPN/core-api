"""Create one global payment settings row.

Revision ID: 0026
Revises: 0025
"""

import sqlalchemy as sa
from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_payment_settings",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("auto_confirm", sa.Boolean(), nullable=False),
        sa.Column("digits", sa.SmallInteger(), nullable=False),
        sa.Column("window_hours", sa.SmallInteger(), nullable=False),
        sa.Column("key_hash", sa.String(64)),
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
    op.create_index(
        "uq_payment_settings_singleton",
        "tbl_payment_settings",
        [sa.text("(true)")],
        unique=True,
    )
    op.execute(
        "INSERT INTO tbl_payment_settings "
        "(auto_confirm, digits, window_hours) "
        "VALUES (false, 5, 24)"
    )


def downgrade() -> None:
    op.drop_table("tbl_payment_settings")
