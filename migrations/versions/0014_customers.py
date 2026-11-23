"""Store retail customer profiles with optional group membership.

Revision ID: 0014
Revises: 0013
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_customers",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column("name", sa.String(55), nullable=False),
        sa.Column("mobile", sa.String(11), nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=True),
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
            ["group_id"], ["tbl_customer_groups.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_tbl_customers_group_id", "tbl_customers", ["group_id"])
    op.create_index(
        "ix_customers_blocked", "tbl_customers", ["is_blocked", "id"]
    )


def downgrade() -> None:
    op.drop_table("tbl_customers")
