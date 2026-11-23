"""Store pending customer receipts and their image addresses.

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_receipts",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("image_url", sa.String(255), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["tbl_customers.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_tbl_receipts_customer_id", "tbl_receipts", ["customer_id"]
    )
    op.create_index("ix_tbl_receipts_image_url", "tbl_receipts", ["image_url"])


def downgrade() -> None:
    op.drop_table("tbl_receipts")
