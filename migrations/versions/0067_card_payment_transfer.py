"""Link each automatic payment confirmation to its transfer.

Revision ID: 0067
Revises: 0066
"""

import sqlalchemy as sa
from alembic import op

revision = "0067"
down_revision = "0066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tbl_card_payments", sa.Column("transfer_id", sa.BigInteger())
    )
    op.create_foreign_key(
        "tbl_card_payments_transfer_id_fkey",
        "tbl_card_payments",
        "tbl_card_transfers",
        ["transfer_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "tbl_card_payments_transfer_id_key",
        "tbl_card_payments",
        ["transfer_id"],
    )


def downgrade() -> None:
    op.drop_column("tbl_card_payments", "transfer_id")
