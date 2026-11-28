"""Add display ordering for the Xray revision catalog.

Revision ID: 0075
Revises: 0074
"""

import sqlalchemy as sa
from alembic import op

revision = "0075"
down_revision = "0074"
branch_labels = None
depends_on = None

_INDEX = "ix_xray_revisions_display_order"


def upgrade() -> None:
    op.add_column(
        "tbl_xray_revisions", sa.Column("sort_order", sa.BigInteger())
    )
    op.create_index(
        _INDEX,
        "tbl_xray_revisions",
        [sa.text("coalesce(sort_order, -id)"), "id"],
    )


def downgrade() -> None:
    op.drop_index(_INDEX, table_name="tbl_xray_revisions")
    op.drop_column("tbl_xray_revisions", "sort_order")
