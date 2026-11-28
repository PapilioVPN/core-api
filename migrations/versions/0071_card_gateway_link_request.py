"""Record the payment's outbound link creation claim.

Revision ID: 0071
Revises: 0070
"""

import sqlalchemy as sa
from alembic import op

revision = "0071"
down_revision = "0070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_card_gateway_payments",
        sa.Column("link_requested_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_column("tbl_card_gateway_payments", "link_requested_at")
