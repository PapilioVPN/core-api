"""Store the optional reason for rejecting a payment.

Revision ID: 0023
Revises: 0022
"""

import sqlalchemy as sa
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_payments", sa.Column("rejection_reason", sa.String(500))
    )


def downgrade() -> None:
    op.drop_column("tbl_payments", "rejection_reason")
