"""Add display ordering for the managed node registry.

Revision ID: 0080
Revises: 0079
"""

import sqlalchemy as sa
from alembic import op

revision = "0080"
down_revision = "0079"
branch_labels = None
depends_on = None

_INDEX = "ix_nodes_display_order"


def upgrade() -> None:
    op.add_column("tbl_nodes", sa.Column("sort_order", sa.BigInteger()))
    op.create_index(
        _INDEX,
        "tbl_nodes",
        [sa.text("coalesce(sort_order, -id)"), "id"],
    )


def downgrade() -> None:
    op.drop_index(_INDEX, table_name="tbl_nodes")
    op.drop_column("tbl_nodes", "sort_order")
