"""Store the optional reason for rejecting a receipt.

Revision ID: 0022
Revises: 0021
"""

import sqlalchemy as sa
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_receipts", sa.Column("rejection_reason", sa.String(500))
    )


def downgrade() -> None:
    op.drop_column("tbl_receipts", "rejection_reason")
