"""Persist reusable shop volume definitions.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_volumes",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column(
            "mode",
            sa.Enum(
                "fixed",
                "custom",
                name="volumemode",
                native_enum=False,
                length=8,
            ),
            nullable=False,
        ),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("min_bytes", sa.BigInteger(), nullable=True),
        sa.Column("max_bytes", sa.BigInteger(), nullable=True),
        sa.Column("step_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("tbl_volumes")
